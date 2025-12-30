"""Climate controller for Smart Heating - Refactored."""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Any, List, Tuple, Dict

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ..core.area_manager import AreaManager
from ..exceptions import SmartHeatingError
from .device_control import DeviceControlHandler
from .heating_cycle import HeatingCycleHandler
from .protection import ProtectionHandler
from .sensor_monitoring import SensorMonitoringHandler
from .temperature_sensors import TemperatureSensorHandler

_LOGGER = logging.getLogger(__name__)


class ClimateController:
    """Control heating based on area settings and schedules."""

    def __init__(
        self,
        hass: HomeAssistant,
        area_manager: AreaManager,
        learning_engine=None,
        capability_detector=None,
    ) -> None:
        """Initialize the climate controller.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            learning_engine: Optional learning engine for adaptive features
            capability_detector: Optional device capability detector
        """
        self.hass = hass
        self.area_manager = area_manager
        self.learning_engine = learning_engine
        self.capability_detector = capability_detector
        self._hysteresis = 0.5  # Temperature hysteresis in °C

        # Initialize handlers
        self.temp_handler: TemperatureSensorHandler = TemperatureSensorHandler(hass)
        self.device_handler: DeviceControlHandler = DeviceControlHandler(
            hass, area_manager, capability_detector
        )
        self.sensor_handler: Optional[SensorMonitoringHandler] = None  # Set by set_area_logger
        self.protection_handler: Optional[ProtectionHandler] = None  # Set by set_area_logger
        self.cycle_handler: Optional[HeatingCycleHandler] = None  # Set by set_area_logger
        self.area_logger: Optional[Any] = None

    def set_area_logger(self, area_logger: Any) -> None:
        """Set area logger and reinitialize handlers that need it.

        Args:
            area_logger: Area logger instance
        """
        self.area_logger = area_logger
        self.sensor_handler = SensorMonitoringHandler(self.hass, self.area_manager, area_logger)
        self.protection_handler = ProtectionHandler(self.hass, self.area_manager, area_logger)
        self.cycle_handler = HeatingCycleHandler(
            self.hass, self.area_manager, self.learning_engine, area_logger
        )

    # Delegate methods to handlers
    def _get_temperature_from_sensor(self, sensor_id: str) -> Optional[float]:
        """Get temperature from sensor (delegates to handler)."""
        return self.temp_handler.get_temperature_from_sensor(sensor_id)

    def _get_temperature_from_thermostat(self, thermostat_id: str) -> Optional[float]:
        """Get temperature from thermostat (delegates to handler)."""
        return self.temp_handler.get_temperature_from_thermostat(thermostat_id)

    def _collect_area_temperatures(self, area):
        """Collect area temperatures (delegates to handler)."""
        return self.temp_handler.collect_area_temperatures(area)

    def _convert_fahrenheit_to_celsius(self, temp: float) -> float:
        """Convert Fahrenheit to Celsius (delegates to handler)."""
        return self.temp_handler.convert_fahrenheit_to_celsius(temp)

    # _get_temperature_from_sensor already defined above; keep single definition

    def _check_window_sensors(self, area_id: str, area) -> bool:
        """Check window sensors (delegates to handler)."""
        if not self.sensor_handler:
            return False
        return self.sensor_handler.check_window_sensors(area_id, area)

    def _log_window_state_change(self, area_id: str, area, any_window_open: bool) -> None:
        """Log window state change (delegates to handler)."""
        if self.sensor_handler:
            self.sensor_handler.log_window_state_change(area_id, area, any_window_open)

    def _get_presence_sensors_for_area(self, area):
        """Get presence sensors for area (delegates to handler)."""
        if not self.sensor_handler:
            return []
        return self.sensor_handler.get_presence_sensors_for_area(area)

    def _check_presence_sensors(self, area_id: str, sensors: list) -> bool:
        """Check presence sensors (delegates to handler)."""
        if not self.sensor_handler:
            return False
        return self.sensor_handler.check_presence_sensors(area_id, sensors)

    async def _handle_auto_preset_change(self, area_id: str, area, presence: bool) -> None:
        """Handle auto preset change (delegates to handler)."""
        if self.sensor_handler:
            await self.sensor_handler.handle_auto_preset_change(area_id, area, presence)

    async def _async_prepare_heating_cycle(self):
        """Prepare heating cycle (delegates to handler)."""
        if not self.cycle_handler:
            return False, None
        return await self.cycle_handler.async_prepare_heating_cycle(
            self.temp_handler, self.sensor_handler
        )

    def _is_any_thermostat_actively_heating(self, area) -> bool:
        """Check if thermostats are heating (delegates to handler)."""
        return self.device_handler.is_any_thermostat_actively_heating(area)

    def _get_valve_capability(self, entity_id: str):
        """Get valve capability (delegates to handler)."""
        return self.device_handler.get_valve_capability(entity_id)

    def _apply_frost_protection(self, area_id: str, target_temp: float) -> float:
        """Apply frost protection (delegates to handler)."""
        if not self.protection_handler:
            return target_temp
        return self.protection_handler.apply_frost_protection(area_id, target_temp)

    def _apply_vacation_mode(self, area_id: str, area) -> None:
        """Apply vacation mode (delegates to handler)."""
        if self.protection_handler:
            self.protection_handler.apply_vacation_mode(area_id, area)

    async def _async_control_thermostats(
        self, area, heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control thermostats (delegates to handler)."""
        await self.device_handler.async_control_thermostats(area, heating, target_temp)

    async def _async_control_switches(self, area, heating: bool) -> None:
        """Control switches (delegates to handler)."""
        await self.device_handler.async_control_switches(area, heating)

    async def _async_control_valves(
        self, area, heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control valves (delegates to handler)."""
        await self.device_handler.async_control_valves(area, heating, target_temp)

    async def _async_control_opentherm_gateway(
        self, any_heating: bool, max_target_temp: float
    ) -> None:
        """Control OpenTherm gateway (delegates to handler)."""
        await self.device_handler.async_control_opentherm_gateway(any_heating, max_target_temp)

    async def _async_get_outdoor_temperature(self, area):
        """Get outdoor temperature (delegates to handler)."""
        return await self.temp_handler.async_get_outdoor_temperature(area)

    async def _async_handle_manual_override(self, area_id: str, area) -> None:
        """Handle manual override (delegates to handler)."""
        if self.protection_handler:
            await self.protection_handler.async_handle_manual_override(
                area_id, area, self.device_handler
            )

    async def _async_handle_disabled_area(
        self, area_id: str, area, history_tracker, should_record_history: bool
    ) -> None:
        """Handle disabled area (delegates to handler)."""
        if self.protection_handler:
            await self.protection_handler.async_handle_disabled_area(
                area_id,
                area,
                self.device_handler,
                history_tracker,
                should_record_history,
            )

    async def async_update_area_temperatures(
        self,
    ) -> None:  # NOSONAR - intentionally async (awaited by callers)
        """Update current temperatures for all areas from sensors.

        Delegates to centralized temperature handler for consistent behavior.
        """
        await asyncio.sleep(0)
        self.temp_handler.update_all_area_temperatures(self.area_manager)

    async def _async_set_area_heating(
        self, area, heating: bool, target_temp: Optional[float] = None
    ) -> None:
        """Set heating state for an area."""
        await self.device_handler.async_control_thermostats(area, heating, target_temp)
        await self.device_handler.async_control_switches(area, heating)
        await self.device_handler.async_control_valves(area, heating, target_temp)

    async def _process_area(
        self,
        area_id: str,
        area,
        current_time: datetime,
        should_record_history: bool,
        history_tracker,
    ):
        """Process a single area and return heating areas and max target temp.

        Returns:
            Tuple(list of heating area ids, max target temperature)
        """
        await self._record_area_history(area_id, area, should_record_history, history_tracker)

        if await self._handle_disabled_area(area_id, area, history_tracker, should_record_history):
            return None, None

        # Check for manual override mode
        if hasattr(area, "manual_override") and area.manual_override:
            if self.protection_handler:
                await self.protection_handler.async_handle_manual_override(
                    area_id, area, self.device_handler
                )
            else:
                _LOGGER.debug(
                    "No protection handler available to handle manual override for area %s",
                    area_id,
                )
            return None, None

        # Check for vacation mode (applies in place)
        if self.protection_handler:
            self.protection_handler.apply_vacation_mode(area_id, area)

        # Get effective target temperature
        target_temp = self._get_and_log_target_temp(area_id, area, current_time)
        _LOGGER.info(
            "Area %s: Effective target=%.1f°C (boost_active=%s, preset=%s)",
            area_id,
            target_temp,
            area.boost_manager.boost_mode_active,
            area.preset_mode,
        )

        if hasattr(self, "area_logger") and self.area_logger:
            details = {
                "target_temp": target_temp,
                "boost_active": area.boost_manager.boost_mode_active,
                "preset_mode": area.preset_mode,
                "base_target": area.target_temperature,
            }
            self.area_logger.log_event(
                area_id,
                "temperature",
                f"Effective target temperature: {target_temp:.1f}°C",
                details,
            )

        # Apply frost protection
        target_temp = self._apply_frost_protection(area_id, target_temp)

        # Apply HVAC mode - turn off thermostats when hvac_mode is "off"
        if await self._handle_hvac_off(area_id, area):
            return None, None

        current_temp = area.current_temperature
        if current_temp is None:
            return None, None

        # Calculate modes and thresholds
        (
            hysteresis,
            hvac_mode,
            heating,
            cooling,
            should_stop_heat,
            should_stop_cool,
        ) = self._calculate_modes(area, current_temp, target_temp)

        self._log_hysteresis_if_needed(
            area_id, area, current_temp, target_temp, hysteresis, heating, cooling
        )

        return await self._handle_cycle_actions(
            area_id,
            area,
            current_temp,
            target_temp,
            heating,
            cooling,
            should_stop_heat,
            should_stop_cool,
        )

    async def _handle_hvac_off(self, area_id: str, area) -> bool:
        """Handle HVAC off mode for an area and return True if processing should stop."""
        if hasattr(area, "hvac_mode") and area.hvac_mode == "off":
            _LOGGER.info("Area %s: HVAC mode is OFF - turning off all thermostats", area_id)
            # Turn off all thermostats in the area
            thermostats = area.get_thermostats()
            for thermostat_id in thermostats:
                try:
                    await self.device_handler._handle_thermostat_turn_off(thermostat_id)
                    _LOGGER.debug("Turned off thermostat %s in area %s", thermostat_id, area_id)
                except (HomeAssistantError, SmartHeatingError, asyncio.TimeoutError) as err:
                    _LOGGER.error("Failed to turn off thermostat %s: %s", thermostat_id, err)
            # Turn off switches and valves too
            await self.device_handler.async_control_switches(area, False)
            await self.device_handler.async_control_valves(area, False, None)
            area.state = "off"
            _LOGGER.debug("Area %s: All climate devices turned off", area_id)
            return True
        return False

    async def _record_area_history(self, area_id, area, should_record_history, history_tracker):
        """Record history if enabled and available."""
        if should_record_history and history_tracker and area.current_temperature is not None:
            trvs = self._collect_trv_states(area)
            await history_tracker.async_record_temperature(
                area_id, area.current_temperature, area.target_temperature, area.state, trvs
            )

    def _collect_trv_states(self, area) -> list[dict]:
        """Collect TRV states for an area's configured TRV entities.

        Returns a list of dicts with keys: entity_id, open, position, running_state
        """
        trv_states: list[dict] = []
        running_state = getattr(area, "state", None)

        for trv in getattr(area, "trv_entities", []):
            entity_id = trv.get("entity_id")
            if not entity_id:
                continue

            trv_data = self._get_single_trv_state(entity_id, running_state)
            if trv_data:
                trv_states.append(trv_data)

        return trv_states

    def _get_single_trv_state(self, entity_id: str, running_state) -> Optional[dict]:
        """Get state data for a single TRV entity."""
        try:
            state = self.hass.states.get(entity_id)
            open_state, position = self._extract_trv_values(entity_id, state)

            return {
                "entity_id": entity_id,
                "open": open_state,
                "position": position,
                "running_state": running_state,
            }
        except (HomeAssistantError, SmartHeatingError, asyncio.TimeoutError):
            return None

    def _extract_trv_values(self, entity_id: str, state) -> tuple[Optional[bool], Optional[float]]:
        """Extract open state and position from TRV entity state."""
        if not state or state.state in ("unknown", "unavailable"):
            return None, None

        domain = entity_id.split(".")[0]
        if domain == "binary_sensor":
            return state.state in ("on", "open"), None

        return None, self._get_valve_position(state)

    def _get_valve_position(self, state) -> Optional[float]:
        """Extract valve position from state or attributes."""
        try:
            return float(state.state)
        except (ValueError, TypeError):
            pass

        for attr in ("position", "valve_position", "current_position"):
            if attr in state.attributes:
                try:
                    return float(state.attributes.get(attr))
                except (ValueError, TypeError):
                    continue
        return None

    async def _handle_disabled_area(self, area_id, area, history_tracker, should_record_history):
        """Handle an area that is disabled and return True if processing should stop."""
        if not area.enabled:
            if self.protection_handler:
                await self.protection_handler.async_handle_disabled_area(
                    area_id,
                    area,
                    self.device_handler,
                    history_tracker,
                    should_record_history,
                )
            else:
                _LOGGER.debug(
                    "No protection handler available to handle disabled area %s",
                    area_id,
                )
            return True
        return False

    def _get_and_log_target_temp(self, area_id, area, current_time):
        """Get effective target temperature and emit logs if present."""
        target_temp = area.get_effective_target_temperature(current_time)
        _LOGGER.info(
            "Area %s: Effective target=%.1f°C (boost_active=%s, preset=%s)",
            area_id,
            target_temp,
            area.boost_manager.boost_mode_active,
            area.preset_mode,
        )
        if hasattr(self, "area_logger") and self.area_logger:
            details = {
                "target_temp": target_temp,
                "boost_active": area.boost_manager.boost_mode_active,
                "preset_mode": area.preset_mode,
                "base_target": area.target_temperature,
            }
            self.area_logger.log_event(
                area_id,
                "temperature",
                f"Effective target temperature: {target_temp:.1f}°C",
                details,
            )
        return target_temp

    def _calculate_modes(self, area, current_temp, target_temp):
        """Calculate hysteresis and determine heating/cooling flags."""
        hysteresis = (
            area.hysteresis_override if area.hysteresis_override is not None else self._hysteresis
        )
        hvac_mode = area.hvac_mode if hasattr(area, "hvac_mode") else "heat"
        should_heat = current_temp < (target_temp - hysteresis)
        should_cool = current_temp > (target_temp + hysteresis)
        should_stop_heat = current_temp >= target_temp
        should_stop_cool = current_temp <= target_temp
        heating = hvac_mode in ["heat", "heat_cool", "auto"] and should_heat
        cooling = hvac_mode in ["cool", "heat_cool", "auto"] and should_cool
        return (
            hysteresis,
            hvac_mode,
            heating,
            cooling,
            should_stop_heat,
            should_stop_cool,
        )

    def _log_hysteresis_if_needed(
        self, area_id, area, current_temp, target_temp, hysteresis, heating, cooling
    ):
        """Log hysteresis waiting if no active heating/cooling action is required."""
        if hasattr(self, "area_logger") and self.area_logger:
            if not heating and not cooling and current_temp != target_temp:
                reason = "Within hysteresis band - prevents short cycling"
                if abs(current_temp - target_temp) <= hysteresis:
                    self.area_logger.log_event(
                        area_id,
                        "climate_control",
                        f"Waiting for hysteresis ({hysteresis:.1f}°C) - no action",
                        {
                            "current_temp": current_temp,
                            "target_temp": target_temp,
                            "hysteresis": hysteresis,
                            "heat_threshold": target_temp - hysteresis,
                            "cool_threshold": target_temp + hysteresis,
                            "hvac_mode": (area.hvac_mode if hasattr(area, "hvac_mode") else "heat"),
                            "reason": reason,
                        },
                    )

    async def _handle_cycle_actions(
        self,
        area_id,
        area,
        current_temp,
        target_temp,
        heating,
        cooling,
        should_stop_heat,
        should_stop_cool,
    ):
        """Handle the cycle action based on heating/cooling flags.

        Uses state transition tracking to only call handlers when heating state changes.

        Returns:
            Tuple of (heating_areas, max_temp) or (None, None)
        """
        last_state = getattr(area, "_last_heating_state", None)

        if heating:
            return await self._handle_heating_transition(
                area, area_id, current_temp, target_temp, last_state
            )

        if cooling:
            await self._handle_cooling_transition(
                area, area_id, current_temp, target_temp, last_state
            )
            return [], None

        if should_stop_heat:
            await self._handle_stop_heating_transition(
                area, area_id, current_temp, target_temp, last_state
            )
            return [], None

        if should_stop_cool:
            await self._handle_stop_cooling_transition(area, area_id, current_temp, last_state)
            return [], None

        return [], None

    async def _handle_heating_transition(
        self, area, area_id, current_temp, target_temp, last_state
    ):
        """Handle transition to heating state.

        Returns:
            Tuple of (heating_areas, max_temp)
        """
        if last_state != True:
            # STATE TRANSITION: idle/unknown → heating
            _LOGGER.info(
                "Area %s: STATE TRANSITION → heating (%.1f°C → %.1f°C)",
                area_id,
                current_temp,
                target_temp,
            )
            area._last_heating_state = True
            if self.cycle_handler:
                return await self.cycle_handler.async_handle_heating_required(
                    area_id, area, current_temp, target_temp, self.device_handler, self.temp_handler
                )
            _LOGGER.warning(
                "No cycle handler available to process heating transition for area %s",
                area_id,
            )
            heating_areas = [] if getattr(area, "heating_type", "radiator") == "airco" else [area]
            return heating_areas, target_temp

        # Already heating - skip handler call
        _LOGGER.debug(
            "Area %s: Already heating (%.1f°C → %.1f°C) - no handler call",
            area_id,
            current_temp,
            target_temp,
        )
        heating_areas = [] if getattr(area, "heating_type", "radiator") == "airco" else [area]
        return heating_areas, target_temp

    async def _handle_cooling_transition(
        self, area, area_id, current_temp, target_temp, last_state
    ):
        """Handle transition to cooling state."""
        if last_state != "cooling":
            # STATE TRANSITION: → cooling
            _LOGGER.info(
                "Area %s: STATE TRANSITION → cooling (%.1f°C → %.1f°C)",
                area_id,
                current_temp,
                target_temp,
            )
            area._last_heating_state = "cooling"
            if self.cycle_handler:
                await self.cycle_handler.async_handle_cooling_required(
                    area_id, area, current_temp, target_temp, self.device_handler, self.temp_handler
                )
            else:
                _LOGGER.warning(
                    "No cycle handler available to process cooling transition for area %s",
                    area_id,
                )
        else:
            # Already cooling - skip handler call
            _LOGGER.debug(
                "Area %s: Already cooling (%.1f°C) - no handler call", area_id, current_temp
            )

    async def _handle_stop_heating_transition(
        self, area, area_id, current_temp, target_temp, last_state
    ):
        """Handle transition from heating to idle state."""
        if last_state != False:
            # STATE TRANSITION: heating → idle
            _LOGGER.info(
                "Area %s: STATE TRANSITION → idle (%.1f°C ≥ %.1f°C)",
                area_id,
                current_temp,
                target_temp,
            )
            area._last_heating_state = False
            if self.cycle_handler:
                await self.cycle_handler.async_handle_heating_stop(
                    area_id, area, current_temp, target_temp, self.device_handler
                )
            else:
                _LOGGER.warning(
                    "No cycle handler available to process heating stop for area %s",
                    area_id,
                )
        else:
            # Already idle - skip handler call
            _LOGGER.debug("Area %s: Already idle (%.1f°C) - no handler call", area_id, current_temp)

    async def _handle_stop_cooling_transition(self, area, area_id, current_temp, last_state):
        """Handle transition from cooling to idle state."""
        if last_state != False:
            # STATE TRANSITION: cooling → idle
            _LOGGER.info(
                "Area %s: STATE TRANSITION → idle (cooling stopped at %.1f°C)",
                area_id,
                current_temp,
            )
            area._last_heating_state = False
            if self.cycle_handler:
                target_temp = getattr(area, "target_temperature", current_temp)
                await self.cycle_handler.async_handle_cooling_stop(
                    area_id, area, current_temp, target_temp, self.device_handler
                )
            else:
                _LOGGER.warning(
                    "No cycle handler available to process cooling stop for area %s",
                    area_id,
                )
        else:
            # Already idle - skip handler call
            _LOGGER.debug("Area %s: Already idle - no handler call", area_id)

    async def async_control_heating(self) -> None:
        """Control heating for all areas based on temperature and schedules."""
        if not self.cycle_handler or not self.protection_handler:
            _LOGGER.error("Handlers not initialized - call set_area_logger first")
            return

        current_time = datetime.now()

        # Prepare for heating cycle
        (
            should_record_history,
            history_tracker,
        ) = await self.cycle_handler.async_prepare_heating_cycle(
            self.temp_handler, self.sensor_handler
        )

        # Track heating demands across all areas
        heating_areas = []
        max_target_temp = 0.0

        # Control each area
        for area_id, area in self.area_manager.get_all_areas().items():
            area_heating, area_max_temp = await self._process_area(
                area_id,
                area,
                current_time,
                should_record_history,
                history_tracker,
            )
            if area_heating is not None:
                heating_areas.extend(area_heating)
            if area_max_temp is not None:
                max_target_temp = max(max_target_temp, area_max_temp)

        # Control OpenTherm gateway
        await self.device_handler.async_control_opentherm_gateway(
            len(heating_areas) > 0, max_target_temp
        )

        # Save history periodically
        if should_record_history and history_tracker:
            await history_tracker.async_save()
