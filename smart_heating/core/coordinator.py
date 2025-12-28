"""DataUpdateCoordinator for the Smart Heating integration."""

import asyncio
import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..const import DOMAIN, STATE_INITIALIZED, UPDATE_INTERVAL
from ..exceptions import SmartHeatingError, ValidationError
from ..models import Area
from .area_manager import AreaManager
from .coordination.debouncer import Debouncer
from .coordination.manual_override_detector import ManualOverrideDetector
from .coordination.state_builder import StateBuilder
from .coordination.temperature_tracker import TemperatureTracker

_LOGGER = logging.getLogger(__name__)

# Debounce delay for manual temperature changes (in seconds)
MANUAL_TEMP_CHANGE_DEBOUNCE = 2.0


class SmartHeatingCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Smart Heating data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, area_manager: AreaManager) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            entry: Config entry
            area_manager: Zone manager instance
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
        )
        self.area_manager = area_manager
        self._unsub_state_listener = None
        self._refresh_tasks = set()  # Track outstanding refresh tasks

        # Create coordination components
        self._state_builder = StateBuilder(hass, self)
        self._debouncer = Debouncer(delay=MANUAL_TEMP_CHANGE_DEBOUNCE)
        self._manual_override_detector = ManualOverrideDetector(startup_grace_period_active=True)
        self._temperature_tracker = TemperatureTracker()

        _LOGGER.debug("Smart Heating coordinator initialized")

    async def async_setup(self) -> None:
        """Set up the coordinator with state change listeners."""
        _LOGGER.debug("Coordinator async_setup called")
        # Get all device entity IDs that we need to track
        tracked_entities = []
        areas = self.area_manager.get_all_areas()
        _LOGGER.info("Found %d areas to process", len(areas))
        for area in areas.values():
            for device_id in area.devices.keys():
                tracked_entities.append(device_id)

        if tracked_entities:
            _LOGGER.info(
                "Setting up state change listeners for %d devices: %s",
                len(tracked_entities),
                tracked_entities[:5],
            )
            self._unsub_state_listener = async_track_state_change_event(
                self.hass, tracked_entities, self._handle_state_change
            )
            _LOGGER.debug("State change listeners successfully registered")
        else:
            _LOGGER.debug("No devices found to track for state changes")

        # Do initial update
        await self.async_refresh()

        # End startup grace period after 10 seconds
        # This prevents false manual override triggers from stale thermostat states
        async def end_grace_period():
            await asyncio.sleep(10)
            self._manual_override_detector.set_startup_grace_period(False)

        self._grace_period_task = asyncio.create_task(end_grace_period())
        _LOGGER.debug("Coordinator async_setup completed")

    @callback
    def _should_update_for_state_change(self, entity_id: str, old_state, new_state) -> bool:
        """Determine if a state change should trigger coordinator update.

        Args:
            entity_id: Entity ID that changed
            old_state: Previous state
            new_state: New state

        Returns:
            True if update should be triggered
        """
        if old_state is None:
            # Initial state, trigger update
            return True

        if old_state.state != new_state.state:
            # State changed
            _LOGGER.debug(
                "State changed for %s: %s -> %s",
                entity_id,
                old_state.state,
                new_state.state,
            )
            return True

        if old_state.attributes.get("current_temperature") != new_state.attributes.get(
            "current_temperature"
        ):
            # Current temperature changed
            _LOGGER.debug(
                "Current temperature changed for %s: %s -> %s",
                entity_id,
                old_state.attributes.get("current_temperature"),
                new_state.attributes.get("current_temperature"),
            )
            return True

        if old_state.attributes.get("hvac_action") != new_state.attributes.get("hvac_action"):
            # HVAC action changed (heating/idle/off)
            _LOGGER.info(
                "HVAC action changed for %s: %s -> %s",
                entity_id,
                old_state.attributes.get("hvac_action"),
                new_state.attributes.get("hvac_action"),
            )
            return True

        return False

    def _handle_temperature_change(self, entity_id: str, old_state, new_state) -> None:
        """Handle debounced temperature changes from thermostats.

        Args:
            entity_id: Entity ID
            old_state: Previous state
            new_state: New state
        """
        new_temp = new_state.attributes.get("temperature")
        old_temp = old_state.attributes.get("temperature")

        _LOGGER.debug(
            "Thermostat temperature change detected for %s: %s -> %s (debouncing)",
            entity_id,
            old_temp,
            new_temp,
        )

        # Debounce the temperature change
        async def apply_and_refresh():
            """Apply temperature change and refresh coordinator."""
            _LOGGER.debug(
                "Applying debounced temperature change for %s: %s",
                entity_id,
                new_temp,
            )

            await self._apply_manual_temperature_change(entity_id, new_temp)

            # Force immediate coordinator refresh after debounce (not rate-limited)
            _LOGGER.debug("Forcing coordinator refresh after debounce")
            await self.async_refresh()
            _LOGGER.debug("Coordinator refresh completed")

        # Use debouncer to handle the temperature change
        # Create task to await debounce (returns immediately after starting debounce task)
        import asyncio

        async def start_debounce():
            await self._debouncer.async_debounce(entity_id, apply_and_refresh)

        # Save task reference to prevent garbage collection (S7502)
        task = asyncio.create_task(start_debounce())
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    async def _apply_manual_temperature_change(self, entity_id: str, new_temp: float) -> None:
        """Apply manual temperature change to area - delegates to ManualOverrideDetector.

        Args:
            entity_id: Thermostat entity ID
            new_temp: New temperature set by user
        """
        await self._manual_override_detector.async_detect_and_apply_override(
            entity_id, new_temp, self.area_manager
        )

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle state changes of tracked entities.

        Args:
            event: State change event
        """
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if not new_state:
            return

        # Check for target temperature changes (for thermostats) - handle with debouncing
        if old_state and old_state.attributes.get("temperature") != new_state.attributes.get(
            "temperature"
        ):
            self._handle_temperature_change(entity_id, old_state, new_state)
            return  # Don't trigger immediate update - wait for debounce

        # Check if other state changes should trigger update
        if self._should_update_for_state_change(entity_id, old_state, new_state):
            # Trigger immediate coordinator update
            _LOGGER.debug("Triggering coordinator refresh for %s", entity_id)
            import asyncio

            # Schedule a refresh and keep a reference so it doesn't get garbage collected
            try:
                task = asyncio.create_task(self.async_request_refresh())
                self._refresh_tasks.add(task)
                task.add_done_callback(lambda fut: self._refresh_tasks.discard(fut))
            except (RuntimeError, asyncio.CancelledError) as err:
                # If scheduling fails, ignore
                _LOGGER.debug("Failed to schedule refresh task: %s", err)

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and clean up listeners."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None
        # Cancel tasks and clear them using helpers
        self._cancel_task_if_exists("_grace_period_task")
        self._debouncer.cancel_all()
        self._cancel_task_collection(self._refresh_tasks)
        # Let cancellations settle
        try:
            await self.hass.async_block_till_done()
        except (asyncio.CancelledError, RuntimeError) as err:
            # Best-effort wait for cancellations to settle; log and continue on error
            _LOGGER.debug("Error while waiting for tasks to settle: %s", err)
        _LOGGER.debug("Smart Heating coordinator shutdown")

    def _cancel_task_if_exists(self, task_attr: str) -> None:
        """Cancel a single task attribute if present.

        Args:
            task_attr: Name of the attribute on self that holds the task
        """
        try:
            task = getattr(self, task_attr, None)
            if task:
                try:
                    task.cancel()
                except (asyncio.CancelledError, RuntimeError, AttributeError) as err:
                    _LOGGER.debug("Failed to cancel task %s: %s", task_attr, err)
                setattr(self, task_attr, None)
        except (AttributeError, TypeError) as err:
            _LOGGER.debug("Error inspecting task attribute %s: %s", task_attr, err)

    def _cancel_task_collection(self, tasks: dict | set) -> None:
        """Cancel tasks inside a collection (dict or set) and clear it.

        Args:
            tasks: Collection of tasks (dict of name->task or set of tasks)
        """
        try:
            if isinstance(tasks, dict):
                iterable = list(tasks.values())
            else:
                iterable = list(tasks)
            for t in iterable:
                try:
                    t.cancel()
                except (asyncio.CancelledError, RuntimeError, AttributeError) as err:
                    _LOGGER.debug("Failed to cancel tracked task: %s", err)
            # Clear collection safely
            try:
                tasks.clear()
            except (AttributeError, TypeError, RuntimeError) as err:
                _LOGGER.debug("Failed to clear task collection: %s", err)
        except (AttributeError, TypeError, ValueError) as err:
            _LOGGER.debug("Error cancelling task collection: %s", err)

    def _get_device_state_data(self, device_id: str, device_info: dict) -> dict:
        """Get state data for a single device.

        Args:
            device_id: Device entity ID
            device_info: Device information from area

        Returns:
            Device state data dictionary
        """
        state = self.hass.states.get(device_id)
        device_data = {
            "id": device_id,
            "type": device_info["type"],
            "state": state.state if state else "unavailable",
            "name": (state.attributes.get("friendly_name", device_id) if state else device_id),
        }

        if not state:
            return device_data

        # Add device-specific attributes based on type
        if device_info["type"] == "thermostat":
            device_data.update(
                {
                    "current_temperature": state.attributes.get("current_temperature"),
                    "target_temperature": state.attributes.get("temperature"),
                    "hvac_action": state.attributes.get("hvac_action"),
                }
            )
        elif device_info["type"] == "temperature_sensor":
            device_data["temperature"] = self._get_temperature_from_sensor(device_id, state)
        elif device_info["type"] == "valve":
            device_data["position"] = self._get_valve_position(state)

        return device_data

    def _get_temperature_from_sensor(self, device_id: str, state) -> Optional[float]:
        """Extract and convert temperature from sensor state.

        Args:
            device_id: Sensor entity ID
            state: Home Assistant state object

        Returns:
            Temperature in Celsius or None
        """
        try:
            temp_value = (
                float(state.state) if state.state not in ("unknown", "unavailable") else None
            )
            if temp_value is None:
                return None

            # Check if temperature is in Fahrenheit and convert to Celsius
            unit = state.attributes.get("unit_of_measurement", "°C")
            if unit in ("°F", "F"):
                temp_value = (temp_value - 32) * 5 / 9
                _LOGGER.debug(
                    "Converted temperature sensor %s: %s°F -> %.1f°C",
                    device_id,
                    state.state,
                    temp_value,
                )
            return temp_value
        except (ValueError, TypeError):
            return None

    def _get_valve_position(self, state) -> Optional[float]:
        """Extract valve position from state.

        Args:
            state: Home Assistant state object

        Returns:
            Valve position or None
        """
        try:
            return float(state.state) if state.state not in ("unknown", "unavailable") else None
        except (ValueError, TypeError):
            return None

    def _get_weather_state_data(self, weather_entity_id: str) -> dict | None:
        """Get weather state data for an area.

        Args:
            weather_entity_id: Weather entity ID

        Returns:
            Weather state data dictionary or None
        """
        if not weather_entity_id:
            return None

        state = self.hass.states.get(weather_entity_id)
        if not state or state.state in ("unavailable", "unknown"):
            return None

        try:
            return {
                "entity_id": weather_entity_id,
                "temperature": float(state.state),
                "attributes": dict(state.attributes),
            }
        except (ValueError, TypeError):
            _LOGGER.debug("Failed to parse weather state for %s", weather_entity_id)
            return None

    def _build_area_data(self, area_id: str, area: Area) -> dict:
        """Build data dictionary for a single area - delegates to StateBuilder.

        This method was 97 lines - now it's 3 lines!

        Args:
            area_id: Area identifier
            area: Area instance

        Returns:
            Area data dictionary
        """
        return self._state_builder.build_area_data(area_id, area)

    def _get_trv_states_for_area(self, area: Area) -> list[dict]:
        """Collect TRV states for configured TRV entities in an area.

        Returns a list of dicts with keys: entity_id, open, position, running_state
        """
        trv_states: list[dict] = []
        for trv in getattr(area, "trv_entities", []):
            trv_state = self._parse_trv_state(trv, area)
            if trv_state:
                trv_states.append(trv_state)
        return trv_states

    def _parse_trv_state(self, trv: dict, area: Area) -> dict | None:
        """Parse TRV state from entity.

        Args:
            trv: TRV configuration dict
            area: Area instance

        Returns:
            TRV state dict or None if invalid
        """
        entity_id = trv.get("entity_id")
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        open_state, position = self._extract_trv_values(entity_id, state)

        return {
            "entity_id": entity_id,
            "open": open_state,
            "position": position,
            "running_state": getattr(area, "state", None),
        }

    def _extract_trv_values(self, entity_id: str, state) -> tuple[bool | None, float | None]:
        """Extract open state and position from TRV entity.

        Args:
            entity_id: Entity ID
            state: Home Assistant state object

        Returns:
            Tuple of (open_state, position)
        """
        try:
            domain = entity_id.split(".")[0]
            if domain == "binary_sensor":
                return self._extract_binary_sensor_state(state), None
            return None, self._extract_position(state)
        except (AttributeError, KeyError, ValueError, TypeError) as err:
            # Best-effort only; skip problematic entity
            _LOGGER.debug("Failed to extract window/door state for %s: %s", entity_id, err)
            return None, None

    def _extract_binary_sensor_state(self, state) -> bool | None:
        """Extract binary sensor state.

        Args:
            state: Home Assistant state object

        Returns:
            True if on/open, False if off/closed, None if unavailable
        """
        if state and state.state not in ("unknown", "unavailable"):
            return state.state in ("on", "open")
        return None

    def _extract_position(self, state) -> float | None:
        """Extract valve position from state.

        Args:
            state: Home Assistant state object

        Returns:
            Position as float or None
        """
        if not state or state.state in ("unknown", "unavailable"):
            return None

        # Try state value first
        try:
            return float(state.state)
        except (ValueError, TypeError):
            pass

        # Check common attributes for valve position
        for attr in ("position", "valve_position", "current_position"):
            if attr in state.attributes:
                try:
                    return float(state.attributes.get(attr))
                except (ValueError, TypeError):
                    continue

        return None

    def _get_opentherm_gateway_state(self, gateway_id: str) -> dict | None:
        """Get OpenTherm gateway state data.

        Args:
            gateway_id: OpenTherm gateway entity ID

        Returns:
            Gateway state data dictionary or None
        """
        if not gateway_id:
            return None

        state = self.hass.states.get(gateway_id)
        if not state:
            return None

        # Extract modulation level from attributes
        mod_level = None
        if "relative_mod_level" in state.attributes:
            try:
                mod_level = float(state.attributes["relative_mod_level"])
            except (ValueError, TypeError):
                pass
        elif "modulation_level" in state.attributes:
            try:
                mod_level = float(state.attributes["modulation_level"])
            except (ValueError, TypeError):
                pass

        return {
            "entity_id": gateway_id,
            "state": state.state,
            "modulation_level": mod_level,
            "attributes": dict(state.attributes),
        }

    async def async_enable_area(self, area_id: str) -> None:
        """Enable area and update devices immediately.

        Args:
            area_id: Area identifier

        Raises:
            ValueError: If area does not exist
        """
        from ..const import DOMAIN

        # Enable area in manager
        self.area_manager.enable_area(area_id)
        await self.area_manager.async_save()

        # Proactively update devices for immediate UX
        climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            area = self.area_manager.get_area(area_id)
            if area and area.current_temperature is not None:
                target = area.get_effective_target_temperature()
                heating_needed = area.current_temperature < target

                _LOGGER.info(
                    "Area %s enabled: current=%.1f°C, target=%.1f°C, heating_needed=%s",
                    area_id,
                    area.current_temperature,
                    target,
                    heating_needed,
                )

                # Update thermostats and valves with appropriate heating state
                await climate_controller.device_handler.async_control_thermostats(
                    area, heating_needed, target
                )
                await climate_controller.device_handler.async_control_valves(
                    area, heating_needed, target
                )

        # Request coordinator refresh
        await self.async_request_refresh()

    async def async_disable_area(self, area_id: str) -> None:
        """Disable area and turn off devices immediately.

        Args:
            area_id: Area identifier

        Raises:
            ValueError: If area does not exist
        """
        from ..const import DOMAIN

        # Disable area in manager
        self.area_manager.disable_area(area_id)
        await self.area_manager.async_save()

        # Proactively update devices for immediate UX
        climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            area = self.area_manager.get_area(area_id)
            if area:
                # Use explicit off for valves (0°C) to ensure TRVs close
                await climate_controller.device_handler.async_set_valves_to_off(area, 0.0)
                # Turn off thermostats
                await climate_controller.device_handler.async_control_thermostats(area, False, None)

        # Request coordinator refresh
        await self.async_request_refresh()

    async def _async_update_data(
        self,
    ) -> dict:  # NOSONAR - intentionally async (awaited by DataUpdateCoordinator)
        """Fetch data from the integration.

        This is the place to fetch and process the data from your source.
        Updates area temperatures from MQTT devices.

        Returns:
            dict: Dictionary containing the current state

        Raises:
            UpdateFailed: If update fails
        """
        try:
            _LOGGER.debug("Coordinator update data called")

            # Get all areas
            areas = self.area_manager.get_all_areas()
            _LOGGER.debug("Processing %d areas for coordinator update", len(areas))

            # Get OpenTherm gateway state if configured
            gateway_state = self._get_opentherm_gateway_state(
                self.area_manager.opentherm_gateway_id
            )

            # Build data structure
            data = {
                "status": STATE_INITIALIZED,
                "area_count": len(areas),
                "areas": {},
                "opentherm_gateway": gateway_state,
            }

            # Add area information with device states
            for area_id, area in areas.items():
                data["areas"][area_id] = self._build_area_data(area_id, area)

            _LOGGER.debug("Smart Heating data updated successfully: %d areas", len(areas))
            return data

        except (
            HomeAssistantError,
            SmartHeatingError,
            ValidationError,
            AttributeError,
            KeyError,
        ) as err:
            _LOGGER.error("Error updating Smart Heating data: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
