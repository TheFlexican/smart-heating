"""Thermostat device handler."""

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate.const import SERVICE_SET_TEMPERATURE
from homeassistant.const import ATTR_TEMPERATURE, SERVICE_TURN_OFF, SERVICE_TURN_ON

from .base_device_handler import BaseDeviceHandler

if TYPE_CHECKING:
    from ...models import Area

_LOGGER = logging.getLogger(__name__)


class ThermostatHandler(BaseDeviceHandler):
    """Handle thermostat device operations."""

    def __init__(self, hass, area_manager, capability_detector=None):
        """Initialize thermostat handler."""
        super().__init__(hass, area_manager, capability_detector)
        self._last_set_temperatures: dict[str, float] = {}
        self._last_set_hvac_modes: dict[str, str] = {}

    def is_any_thermostat_actively_heating(self, area: "Area") -> bool:
        """Check if any thermostat in the area is actively heating.

        This checks the hvac_action attribute to determine actual heating state.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "heating"
        """
        thermostats = area.get_thermostats()
        for thermostat_id in thermostats:
            state = self.hass.states.get(thermostat_id)
            if state and state.attributes.get("hvac_action") == "heating":
                return True
        return False

    def is_any_thermostat_actively_cooling(self, area: "Area") -> bool:
        """Check if any thermostat in the area is actively cooling.

        This checks the hvac_action attribute to determine actual cooling state.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "cooling"
        """
        thermostats = area.get_thermostats()
        for thermostat_id in thermostats:
            state = self.hass.states.get(thermostat_id)
            if state and state.attributes.get("hvac_action") == "cooling":
                return True
        return False

    async def _turn_on_switch_and_wait(self, switch_id: str, climate_entity_id: str) -> bool:
        """Turn on a power switch and wait for it to report 'on'.

        Returns True if the switch is or becomes 'on' within the timeout window.
        """
        try:
            state = self.hass.states.get(switch_id)
            if state and getattr(state, "state", None) != "on":
                _LOGGER.info(
                    "Turning on power switch %s for climate entity %s",
                    switch_id,
                    climate_entity_id,
                )
                try:
                    payload = {"entity_id": switch_id}
                    # Best-effort record of the outgoing service call
                    try:
                        self._record_device_event(
                            switch_id,
                            "sent",
                            "switch.turn_on",
                            {"domain": "switch", "service": "turn_on", "data": payload},
                        )
                    except Exception:
                        _LOGGER.debug("Failed to record sent event for switch %s", switch_id)

                    await self.hass.services.async_call(
                        "switch",
                        "turn_on",
                        payload,
                        blocking=False,
                    )
                except Exception:
                    _LOGGER.debug("Failed to call turn_on for switch %s", switch_id)

                for _ in range(6):
                    await asyncio.sleep(0.25)
                    state = self.hass.states.get(switch_id)
                    if state and getattr(state, "state", None) == "on":
                        _LOGGER.debug("Power switch %s is now on", switch_id)
                        return True
                return False
            else:
                _LOGGER.debug(
                    "Power switch %s already on for %s",
                    switch_id,
                    climate_entity_id,
                )
                return True
        except Exception:
            _LOGGER.debug("Error while turning on switch %s", switch_id)
            return False

    async def _set_hvac_mode_if_needed(
        self, thermostat_id: str, desired_mode: str, current_mode: Optional[str], hvac_mode_str: str
    ) -> None:
        """Set HVAC mode if it differs from the current mode (best-effort).

        Uses the current device state as the authoritative source. A cache is used
        as a fallback when device state is unknown/unavailable to avoid sending
        redundant HVAC mode commands.

        If the device reports a different mode than desired, we always send the
        command to ensure external changes are overridden.
        """
        # Check current device state first - this is authoritative
        if current_mode == desired_mode:
            _LOGGER.debug(
                "Thermostat %s already in %s mode (device state), skipping",
                thermostat_id,
                hvac_mode_str,
            )
            return

        # Device state doesn't match desired mode, or state is unknown
        # Use cache as fallback only when device state is unknown/unavailable
        if current_mode is None:
            cached_mode = self._last_set_hvac_modes.get(thermostat_id)
            if cached_mode == desired_mode:
                _LOGGER.debug(
                    "Thermostat %s HVAC mode already set to %s (cached, device state unknown), skipping",
                    thermostat_id,
                    hvac_mode_str,
                )
                return

        # Mode needs to be changed - update cache and send command
        try:
            self._last_set_hvac_modes[thermostat_id] = desired_mode
            payload = {"entity_id": thermostat_id, "hvac_mode": desired_mode}
            try:
                self._record_device_event(
                    thermostat_id,
                    "sent",
                    "climate.set_hvac_mode",
                    {"domain": CLIMATE_DOMAIN, "service": "set_hvac_mode", "data": payload},
                )
            except Exception:
                _LOGGER.debug("Failed to record sent hvac_mode event for %s", thermostat_id)

            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                "set_hvac_mode",
                payload,
                blocking=False,
            )
            try:
                self._record_device_event(
                    thermostat_id,
                    "received",
                    "climate.set_hvac_mode",
                    {"result": "dispatched"},
                )
            except Exception:
                _LOGGER.debug("Failed to record received hvac_mode event for %s", thermostat_id)

            _LOGGER.debug("Set thermostat %s to %s mode", thermostat_id, hvac_mode_str)
        except Exception as err:
            _LOGGER.debug(
                "Failed to set hvac_mode for %s (may already be in target mode): %s",
                thermostat_id,
                err,
            )

    async def _async_ensure_climate_power_on(self, climate_entity_id: str) -> None:
        """Ensure climate device power switch is on if it exists.

        Some AC units have separate power switches (e.g., switch.xxx_power).
        This method checks for common patterns and turns on the switch if found.

        Args:
            climate_entity_id: Climate entity ID (e.g., climate.air_conditioning_air_care)
        """
        # Extract base name from climate entity
        # climate.air_conditioning_air_care -> air_conditioning_air_care
        if "." not in climate_entity_id:
            return

        base_name = climate_entity_id.split(".", 1)[1]

        # Check for common power switch patterns
        power_switch_patterns = [
            f"switch.{base_name}_power",  # switch.air_conditioning_air_care_power
            f"switch.{base_name}_switch",
            f"switch.{base_name}",
        ]

        for switch_id in power_switch_patterns:
            state = self.hass.states.get(switch_id)
            if state:
                # Found a power switch, ensure it's on
                success = await self._turn_on_switch_and_wait(switch_id, climate_entity_id)
                if not success:
                    _LOGGER.debug("Power switch %s did not become 'on' within timeout", switch_id)
                return  # Found and handled the switch

        # No power switch found, which is normal for most thermostats
        _LOGGER.debug("No power switch found for %s", climate_entity_id)

        # As a fallback, some climate integrations require calling the
        # climate.turn_on service (no separate switch). Try to turn the
        # climate entity itself on if it is currently off.
        try:
            state = self.hass.states.get(climate_entity_id)
            if state and getattr(state, "state", None) != "on":
                _LOGGER.info("Turning on climate entity %s", climate_entity_id)
                try:
                    payload = {"entity_id": climate_entity_id}
                    try:
                        self._record_device_event(
                            climate_entity_id,
                            "sent",
                            "climate.turn_on",
                            {"domain": CLIMATE_DOMAIN, "service": SERVICE_TURN_ON, "data": payload},
                        )
                    except Exception:
                        _LOGGER.debug("Failed to record sent turn_on for %s", climate_entity_id)

                    await self.hass.services.async_call(
                        CLIMATE_DOMAIN,
                        SERVICE_TURN_ON,
                        payload,
                        blocking=False,
                    )
                    try:
                        self._record_device_event(
                            climate_entity_id,
                            "received",
                            "climate.turn_on",
                            {"result": "dispatched"},
                        )
                    except Exception:
                        _LOGGER.debug("Failed to record received turn_on for %s", climate_entity_id)
                except Exception:
                    # Be defensive - do not raise from best-effort fallback
                    _LOGGER.debug(
                        "Failed to turn on climate entity %s (fallback)", climate_entity_id
                    )
        except Exception:
            # Be defensive - do not raise from best-effort fallback
            _LOGGER.debug("Failed to turn on climate entity %s (fallback)", climate_entity_id)

    async def _async_turn_off_climate_power(self, climate_entity_id: str) -> None:
        """Turn off climate device power switch if it exists.

        Args:
            climate_entity_id: Climate entity ID
        """
        # Extract base name from climate entity
        if "." not in climate_entity_id:
            return

        base_name = climate_entity_id.split(".", 1)[1]

        # Check for common power switch patterns
        power_switch_patterns = [
            f"switch.{base_name}_power",
            f"switch.{base_name}_switch",
            f"switch.{base_name}",
        ]

        for switch_id in power_switch_patterns:
            state = self.hass.states.get(switch_id)
            if state:
                # Found a power switch, turn it off
                if state.state == "on":
                    _LOGGER.info(
                        "Turning off power switch %s for climate entity %s",
                        switch_id,
                        climate_entity_id,
                    )
                    try:
                        payload = {"entity_id": switch_id}
                        try:
                            self._record_device_event(
                                switch_id,
                                "sent",
                                "switch.turn_off",
                                {"domain": "switch", "service": "turn_off", "data": payload},
                            )
                        except Exception:
                            _LOGGER.debug("Failed to record sent turn_off for %s", switch_id)

                        await self.hass.services.async_call(
                            "switch",
                            "turn_off",
                            payload,
                            blocking=False,
                        )
                    except Exception as err:
                        # Some integrations reject redundant off commands - ignore
                        try:
                            self._record_device_event(
                                switch_id,
                                "received",
                                "switch.turn_off",
                                {"result": "error"},
                                status="error",
                                error=str(err),
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Failed to record received error for turn_off %s", switch_id
                            )
                        _LOGGER.debug(
                            "Failed to turn off switch %s (may already be off): %s",
                            switch_id,
                            err,
                        )
                else:
                    _LOGGER.debug("Power switch %s already off", switch_id)
                return  # Found and handled the switch

    async def async_control_thermostats(
        self,
        area: "Area",
        heating: bool,
        target_temp: Optional[float],
        hvac_mode: str = "heat",
    ) -> None:
        """Control thermostats in an area.

        Args:
            area: Area to control
            heating: Whether heating/cooling should be active
            target_temp: Target temperature
            hvac_mode: HVAC mode ("heat" or "cool")
        """

        thermostats = area.get_thermostats()

        _LOGGER.debug(
            "async_control_thermostats called: area=%s, heating=%s, target_temp=%s, thermostats=%s",
            getattr(area, "name", "<unknown>"),
            heating,
            target_temp,
            thermostats,
        )

        for thermostat_id in thermostats:
            try:
                _LOGGER.info(
                    "Area %s: Processing thermostat %s (heating=%s target_temp=%s hvac_mode=%s)",
                    getattr(area, "name", "<unknown>"),
                    thermostat_id,
                    heating,
                    target_temp,
                    hvac_mode,
                )
                if heating and target_temp is not None:
                    await self._handle_thermostat_heating(thermostat_id, target_temp, hvac_mode)
                elif target_temp is not None:
                    # Skip hysteresis idle logic for AC/climate areas (hvac_mode != "heat")
                    # AC devices have their own control logic and don't need hysteresis band adjustments
                    area_hvac = getattr(area, "hvac_mode", "heat")
                    if area_hvac == "heat":
                        await self._handle_thermostat_idle(area, thermostat_id, target_temp)
                    else:
                        _LOGGER.debug(
                            "Skipping idle hysteresis for AC area %s (hvac_mode=%s)",
                            getattr(area, "name", "<unknown>"),
                            area_hvac,
                        )
                else:
                    await self._handle_thermostat_turn_off(thermostat_id)
            except Exception as err:
                _LOGGER.error("Failed to control thermostat %s: %s", thermostat_id, err)

    async def _handle_thermostat_heating(
        self, thermostat_id: str, target_temp: float, hvac_mode: str
    ) -> None:
        """Handle thermostat updates when heating/cooling is active.

        This method ensures the power switch is on, sets HVAC mode and
        updates the temperature only when it actually changed.
        For TRV devices, uses heating temperature (target + offset) to ensure valve opens.
        """
        from ...const import HVAC_MODE_COOL, HVAC_MODE_HEAT

        # First, ensure any associated power switch is on
        await self._async_ensure_climate_power_on(thermostat_id)

        # For TRV devices, set to area target temperature
        # TRVs have built-in thermostatic control - they'll close the valve
        # when the room reaches the setpoint. No offset needed!
        if self._is_trv_device(thermostat_id):
            last_temp = self._last_set_temperatures.get(thermostat_id)

            _LOGGER.warning(
                "TRV %s: Setting to area target %.1f°C (TRV will close valve when reached)",
                thermostat_id,
                target_temp,
            )

            if last_temp is None or abs(last_temp - target_temp) >= 0.1:
                try:
                    # Update cache BEFORE service call to prevent false manual override detection
                    self._last_set_temperatures[thermostat_id] = target_temp
                    try:
                        payload = {"entity_id": thermostat_id, ATTR_TEMPERATURE: target_temp}
                        try:
                            self._record_device_event(
                                thermostat_id,
                                "sent",
                                "climate.set_temperature",
                                {
                                    "domain": CLIMATE_DOMAIN,
                                    "service": SERVICE_SET_TEMPERATURE,
                                    "data": payload,
                                },
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Failed to record sent set_temperature for %s", thermostat_id
                            )

                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_TEMPERATURE,
                            payload,
                            blocking=True,
                        )
                        try:
                            self._record_device_event(
                                thermostat_id,
                                "received",
                                "climate.set_temperature",
                                {"result": "ok"},
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Failed to record received set_temperature for %s", thermostat_id
                            )

                        _LOGGER.warning(
                            "TRV %s: SET TO %.1f°C (area target)",
                            thermostat_id,
                            target_temp,
                        )
                    except Exception as err:
                        # Clear cache to allow retry at next cycle
                        if thermostat_id in self._last_set_temperatures:
                            del self._last_set_temperatures[thermostat_id]
                        try:
                            self._record_device_event(
                                thermostat_id,
                                "received",
                                "climate.set_temperature",
                                {"result": "error"},
                                status="error",
                                error=str(err),
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Failed to record error for set_temperature %s", thermostat_id
                            )
                        _LOGGER.warning(
                            "Failed to set TRV %s to %.1f°C: %s (will retry next cycle)",
                            thermostat_id,
                            target_temp,
                            err,
                        )
                except Exception as err:
                    # Clear cache to allow retry at next cycle
                    if thermostat_id in self._last_set_temperatures:
                        del self._last_set_temperatures[thermostat_id]
                    _LOGGER.warning(
                        "Failed to set TRV %s to %.1f°C: %s (will retry next cycle)",
                        thermostat_id,
                        target_temp,
                        err,
                    )
            return

        # Get current state to avoid redundant commands (some integrations reject them)
        current_hvac_mode, current_temp = self._get_thermostat_state(thermostat_id)

        # Set HVAC mode only if it needs to change
        ha_hvac_mode = HVAC_MODE_HEAT if hvac_mode == "heat" else HVAC_MODE_COOL
        await self._set_hvac_mode_if_needed(
            thermostat_id, ha_hvac_mode, current_hvac_mode, hvac_mode
        )

        # Only set temperature when it differs sufficiently from current value
        # Check both cached value and actual entity state for robustness
        last_temp = self._last_set_temperatures.get(thermostat_id)

        if self._should_update_temperature(current_temp, last_temp, target_temp):
            try:
                # Update cache BEFORE service call to prevent false manual override detection
                self._last_set_temperatures[thermostat_id] = target_temp
                try:
                    payload = {"entity_id": thermostat_id, ATTR_TEMPERATURE: target_temp}
                    try:
                        self._record_device_event(
                            thermostat_id,
                            "sent",
                            "climate.set_temperature",
                            {
                                "domain": CLIMATE_DOMAIN,
                                "service": SERVICE_SET_TEMPERATURE,
                                "data": payload,
                            },
                        )
                    except Exception:
                        _LOGGER.debug("Failed to record sent set_temperature for %s", thermostat_id)

                    await self.hass.services.async_call(
                        CLIMATE_DOMAIN,
                        SERVICE_SET_TEMPERATURE,
                        payload,
                        blocking=True,
                    )
                    try:
                        self._record_device_event(
                            thermostat_id, "received", "climate.set_temperature", {"result": "ok"}
                        )
                    except Exception:
                        _LOGGER.debug(
                            "Failed to record received set_temperature for %s", thermostat_id
                        )

                    _LOGGER.debug(
                        "Set thermostat %s to %.1f°C (%s mode)",
                        thermostat_id,
                        target_temp,
                        hvac_mode,
                    )
                except Exception as err:
                    try:
                        self._record_device_event(
                            thermostat_id,
                            "received",
                            "climate.set_temperature",
                            {"result": "error"},
                            status="error",
                            error=str(err),
                        )
                    except Exception:
                        _LOGGER.debug(
                            "Failed to record error for set_temperature %s", thermostat_id
                        )
                    _LOGGER.debug(
                        "Failed to set temperature for %s to %.1f°C: %s",
                        thermostat_id,
                        target_temp,
                        err,
                    )
            except Exception as err:
                # Some integrations reject temperature changes under certain conditions
                _LOGGER.debug(
                    "Failed to set temperature for %s to %.1f°C: %s",
                    thermostat_id,
                    target_temp,
                    err,
                )
        else:
            _LOGGER.debug(
                "Skipping thermostat %s update - already at %.1f°C",
                thermostat_id,
                target_temp,
            )

    async def _handle_thermostat_idle(
        self, area: "Area", thermostat_id: str, target_temp: float
    ) -> None:
        """Handle thermostat updates when area is idle (not actively heating/cooling).

        For TRV devices: Set to trv_idle_temp to force valve closed.
        For regular thermostats, implements hysteresis-aware behavior.
        """
        # For TRV devices, set to trv_idle_temp to force valve closed
        # TRVs use their internal temperature sensor which may differ significantly
        # from external room sensors. Setting to idle temp ensures valve closes
        # regardless of where the room sensor is located.
        if self._is_trv_device(thermostat_id):
            idle_temp = getattr(self.area_manager, "trv_idle_temp", 10.0)
            last_temp = self._last_set_temperatures.get(thermostat_id)

            _LOGGER.debug(
                "TRV %s idle: target=%.1f°C, idle_setpoint=%.1f°C, last_cached=%.1f°C",
                thermostat_id,
                target_temp,
                idle_temp,
                last_temp if last_temp is not None else -999.0,
            )

            if last_temp is None or abs(last_temp - idle_temp) >= 0.1:
                try:
                    # Update cache BEFORE service call to prevent false manual override detection
                    self._last_set_temperatures[thermostat_id] = idle_temp
                    try:
                        payload = {"entity_id": thermostat_id, ATTR_TEMPERATURE: idle_temp}
                        try:
                            self._record_device_event(
                                thermostat_id,
                                "sent",
                                "climate.set_temperature",
                                {
                                    "domain": CLIMATE_DOMAIN,
                                    "service": SERVICE_SET_TEMPERATURE,
                                    "data": payload,
                                },
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Failed to record sent idle set_temperature for %s", thermostat_id
                            )

                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_TEMPERATURE,
                            payload,
                            blocking=True,
                        )
                        try:
                            self._record_device_event(
                                thermostat_id,
                                "received",
                                "climate.set_temperature",
                                {"result": "ok"},
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Failed to record received idle set_temperature for %s",
                                thermostat_id,
                            )

                        _LOGGER.info(
                            "TRV %s: SET TO %.1f°C (idle - forcing valve closed)",
                            thermostat_id,
                            idle_temp,
                        )
                    except Exception as err:
                        # Clear cache to allow retry at next cycle
                        if thermostat_id in self._last_set_temperatures:
                            del self._last_set_temperatures[thermostat_id]
                        try:
                            self._record_device_event(
                                thermostat_id,
                                "received",
                                "climate.set_temperature",
                                {"result": "error"},
                                status="error",
                                error=str(err),
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Failed to record error for idle set_temperature %s", thermostat_id
                            )
                        _LOGGER.warning(
                            "Failed to set TRV %s to idle %.1f°C: %s (will retry next cycle)",
                            thermostat_id,
                            idle_temp,
                            err,
                        )
                except Exception as err:
                    # Clear cache to allow retry at next cycle
                    if thermostat_id in self._last_set_temperatures:
                        del self._last_set_temperatures[thermostat_id]
                    _LOGGER.warning(
                        "Failed to set TRV %s to idle %.1f°C: %s (will retry next cycle)",
                        thermostat_id,
                        idle_temp,
                        err,
                    )
            return

        # For regular thermostats, use hysteresis logic
        hysteresis = self._parse_hysteresis(area)

        current_temp_raw = getattr(area, "current_temperature", None)
        try:
            current_temp = float(current_temp_raw) if current_temp_raw is not None else None
        except Exception:
            current_temp = None

        desired_setpoint = target_temp
        try:
            rhs = float(target_temp) - float(hysteresis)
        except Exception:
            rhs = None

        # If current temp is at or above (target - hysteresis) prefer current temp
        if current_temp is not None and rhs is not None and current_temp >= rhs:
            desired_setpoint = current_temp

        last_temp = self._last_set_temperatures.get(thermostat_id)
        _LOGGER.debug(
            "Thermostat %s idle update: last_temp=%s target_temp=%s desired_setpoint=%s",
            thermostat_id,
            last_temp,
            target_temp,
            desired_setpoint,
        )

        _LOGGER.debug(
            "Computed values: current_temp_raw=%s current_temp=%s hysteresis=%s rhs=%s desired_setpoint=%s last_temp=%s",
            current_temp_raw,
            current_temp,
            hysteresis,
            rhs,
            desired_setpoint,
            last_temp,
        )

        if last_temp is None or abs(last_temp - desired_setpoint) >= 0.1:
            # Update cache BEFORE service call to prevent false manual override detection
            self._last_set_temperatures[thermostat_id] = desired_setpoint
            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {"entity_id": thermostat_id, ATTR_TEMPERATURE: desired_setpoint},
                blocking=True,
            )
            _LOGGER.debug(
                "Updated thermostat %s target to %.1f°C (idle)",
                thermostat_id,
                desired_setpoint,
            )

    def _parse_hysteresis(self, area: "Area") -> float:
        """Return a safe hysteresis value for the area (override or default).

        This avoids accidental numeric conversion of MagicMock objects used in tests.
        """
        val = getattr(area, "hysteresis_override", None)
        if isinstance(val, (int, float)):
            try:
                return float(val)
            except Exception:
                pass
        if isinstance(val, str):
            try:
                return float(val)
            except Exception:
                pass

        am_hyst = getattr(self.area_manager, "hysteresis", None)
        if isinstance(am_hyst, (int, float)):
            try:
                return float(am_hyst)
            except Exception:
                pass
        if isinstance(am_hyst, str):
            try:
                return float(am_hyst)
            except Exception:
                pass

        # Fallback default
        return 0.5

    async def _handle_thermostat_turn_off(self, thermostat_id: str) -> None:
        """Turn off thermostat or fall back to minimum setpoint if turn_off not supported.

        Always turns off the associated power switch if it exists (e.g., for LG ThinQ ACs).
        For TRV devices, sets temperature to trv_idle_temp to close the valve.
        Implements deduplication to prevent redundant commands that drain batteries.
        """
        # DO NOT clear cache - preserve last temperature for deduplication
        # Cache clearing prevented repeated commands from being filtered

        # ALWAYS turn off associated power switch first if it exists
        # This is critical for devices like LG ThinQ AC that have separate power switches
        await self._async_turn_off_climate_power(thermostat_id)

        # For TRV devices, set to trv_idle_temp to close valve (don't use turn_off as many TRVs don't support it)
        if self._is_trv_device(thermostat_id):
            off_temp = getattr(self.area_manager, "trv_idle_temp", 10.0)
            last_temp = self._last_set_temperatures.get(thermostat_id)

            _LOGGER.debug(
                "TRV %s turn_off: off_setpoint=%.1f°C, last_cached=%.1f°C",
                thermostat_id,
                off_temp,
                last_temp if last_temp is not None else -999.0,
            )

            # Only send command if temperature changed or never set
            if last_temp is None or abs(last_temp - off_temp) >= 0.1:
                # Update cache BEFORE service call to prevent false manual override detection
                self._last_set_temperatures[thermostat_id] = off_temp
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_SET_TEMPERATURE,
                    {"entity_id": thermostat_id, ATTR_TEMPERATURE: off_temp},
                    blocking=True,
                )
                _LOGGER.info(
                    "TRV %s: SET TO %.1f°C (turn_off - closing valve)", thermostat_id, off_temp
                )
            else:
                _LOGGER.debug(
                    "TRV %s already at %.1f°C (turn_off) - skipping redundant command",
                    thermostat_id,
                    off_temp,
                )
            return

        # For non-TRV devices, check if device supports turn_off service
        state = self.hass.states.get(thermostat_id)
        supports_turn_off = False

        if state:
            # Check supported features - SUPPORT_TURN_OFF is feature flag 128
            supported_features = state.attributes.get("supported_features", 0)
            supports_turn_off = (supported_features & 128) != 0

        if supports_turn_off:
            try:
                # Use blocking=True so we can catch NotImplementedError
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_TURN_OFF,
                    {"entity_id": thermostat_id},
                    blocking=True,
                )
                _LOGGER.debug("Turned off thermostat %s", thermostat_id)
                return

            except Exception as err:
                _LOGGER.debug(
                    "Failed to turn off thermostat %s: %s, falling back to min temp",
                    thermostat_id,
                    err,
                )

        # Fall back to minimum temperature if turn_off not supported
        min_temp = 5.0
        if self.area_manager.frost_protection_enabled:
            min_temp = self.area_manager.frost_protection_temp

        # Update cache BEFORE service call to prevent false manual override detection
        self._last_set_temperatures[thermostat_id] = min_temp
        await self.hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {"entity_id": thermostat_id, ATTR_TEMPERATURE: min_temp},
            blocking=True,
        )
        _LOGGER.debug(
            "Thermostat %s doesn't support turn_off, set to %.1f°C instead",
            thermostat_id,
            min_temp,
        )
