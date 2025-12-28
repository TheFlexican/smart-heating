"""Temperature setter component for thermostats."""

import logging
from typing import TYPE_CHECKING, Callable, Optional

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate.const import SERVICE_SET_TEMPERATURE
from homeassistant.const import ATTR_TEMPERATURE

from ....const import (
    DEBUG_SENTINEL_TEMP,
    DEFAULT_TRV_IDLE_TEMP,
    SUPPORT_TURN_OFF_FLAG,
    TEMP_COMPARISON_TOLERANCE,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ....models import Area

_LOGGER = logging.getLogger(__name__)

# Service constant
_SERVICE_CLIMATE_SET_TEMPERATURE = "climate.set_temperature"


class TemperatureSetter:
    """Set temperatures for thermostats."""

    def __init__(
        self,
        hass: "HomeAssistant",
        area_manager,
        is_trv_device_func: Callable[[str], bool],
        should_update_temperature_func: Callable,
        record_device_event: Optional[Callable] = None,
    ):
        """Initialize temperature setter.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            is_trv_device_func: Function to check if device is a TRV
            should_update_temperature_func: Function to check if temperature should be updated
            record_device_event: Optional callback to record device events
        """
        self.hass = hass
        self.area_manager = area_manager
        self._is_trv_device = is_trv_device_func
        self._should_update_temperature = should_update_temperature_func
        self._record_device_event = record_device_event
        self._last_set_temperatures: dict[str, float] = {}

    async def set_temperature_for_heating(
        self, thermostat_id: str, target_temp: float, hvac_mode: str, current_temp: Optional[float]
    ) -> None:
        """Set temperature when heating/cooling is active.

        For TRV devices, uses area target temperature (TRV will close valve when reached).
        For regular thermostats, sets the target temperature directly.

        Args:
            thermostat_id: Entity ID of the thermostat
            target_temp: Target temperature
            hvac_mode: HVAC mode string for logging
            current_temp: Current temperature from device state
        """
        # For TRV devices, set to area target temperature
        # TRVs have built-in thermostatic control - they'll close the valve
        # when the room reaches the setpoint. No offset needed!
        if self._is_trv_device(thermostat_id):
            await self._set_trv_temperature(thermostat_id, target_temp, "heating")
            return

        # For regular thermostats, check if update is needed
        last_temp = self._last_set_temperatures.get(thermostat_id)

        if self._should_update_temperature(current_temp, last_temp, target_temp):
            await self._send_temperature_command(thermostat_id, target_temp, hvac_mode)
        else:
            _LOGGER.debug(
                "Skipping thermostat %s update - already at %.1f°C",
                thermostat_id,
                target_temp,
            )

    async def set_temperature_for_idle(
        self, area: "Area", thermostat_id: str, target_temp: float
    ) -> None:
        """Set temperature when area is idle (not actively heating/cooling).

        For TRV devices: Set to trv_idle_temp to force valve closed.
        For regular thermostats, implements hysteresis-aware behavior.

        Args:
            area: Area instance
            thermostat_id: Entity ID of the thermostat
            target_temp: Target temperature
        """
        # For TRV devices, set to trv_idle_temp to force valve closed
        if self._is_trv_device(thermostat_id):
            idle_temp = getattr(self.area_manager, "trv_idle_temp", DEFAULT_TRV_IDLE_TEMP)
            await self._set_trv_temperature(thermostat_id, idle_temp, "idle")
            return

        # For regular thermostats, use hysteresis logic
        desired_setpoint = self._calculate_idle_setpoint(area, target_temp)
        last_temp = self._last_set_temperatures.get(thermostat_id)

        _LOGGER.debug(
            "Thermostat %s idle update: last_temp=%s target_temp=%s desired_setpoint=%s",
            thermostat_id,
            last_temp,
            target_temp,
            desired_setpoint,
        )

        if last_temp is None or abs(last_temp - desired_setpoint) >= TEMP_COMPARISON_TOLERANCE:
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

    async def set_temperature_for_turn_off(self, thermostat_id: str) -> None:
        """Set temperature for turn off state.

        For TRV devices, sets temperature to trv_idle_temp to close the valve.
        For regular thermostats, sets to minimum or frost protection temperature.

        Args:
            thermostat_id: Entity ID of the thermostat
        """
        # For TRV devices, set to trv_idle_temp to close valve
        if self._is_trv_device(thermostat_id):
            off_temp = getattr(self.area_manager, "trv_idle_temp", DEFAULT_TRV_IDLE_TEMP)
            last_temp = self._last_set_temperatures.get(thermostat_id)

            _LOGGER.debug(
                "TRV %s turn_off: off_setpoint=%.1f°C, last_cached=%.1f°C",
                thermostat_id,
                off_temp,
                last_temp if last_temp is not None else DEBUG_SENTINEL_TEMP,
            )

            # Only send command if temperature changed or never set
            if last_temp is None or abs(last_temp - off_temp) >= TEMP_COMPARISON_TOLERANCE:
                # Update cache BEFORE service call
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

        # For non-TRV devices that don't support turn_off, use minimum temperature
        min_temp = 5.0
        if self.area_manager.frost_protection_enabled:
            min_temp = self.area_manager.frost_protection_temp

        # Update cache BEFORE service call
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

    async def _set_trv_temperature(self, thermostat_id: str, temp: float, mode: str) -> None:
        """Set temperature for TRV device with caching and error handling.

        Args:
            thermostat_id: Entity ID of the TRV
            temp: Temperature to set
            mode: Mode string for logging ("heating", "idle", etc.)
        """
        last_temp = self._last_set_temperatures.get(thermostat_id)

        log_msg = {
            "heating": f"TRV {thermostat_id}: Setting to area target {temp:.1f}°C (TRV will close valve when reached)",
            "idle": f"TRV {thermostat_id} idle: target={temp:.1f}°C, idle_setpoint={temp:.1f}°C, last_cached={last_temp if last_temp is not None else DEBUG_SENTINEL_TEMP:.1f}°C",
        }
        if mode in log_msg:
            _LOGGER.warning(log_msg[mode])

        if last_temp is None or abs(last_temp - temp) >= TEMP_COMPARISON_TOLERANCE:
            try:
                # Update cache BEFORE service call to prevent false manual override detection
                self._last_set_temperatures[thermostat_id] = temp
                await self._send_temperature_command(thermostat_id, temp, mode)

                success_msg = {
                    "heating": f"TRV {thermostat_id}: SET TO {temp:.1f}°C (area target)",
                    "idle": f"TRV {thermostat_id}: SET TO {temp:.1f}°C (idle - forcing valve closed)",
                }
                if mode in success_msg:
                    _LOGGER.warning(success_msg[mode])

            except (OSError, RuntimeError, ValueError) as err:
                # Clear cache to allow retry at next cycle
                if thermostat_id in self._last_set_temperatures:
                    del self._last_set_temperatures[thermostat_id]
                _LOGGER.warning(
                    "Failed to set TRV %s to %.1f°C: %s (will retry next cycle)",
                    thermostat_id,
                    temp,
                    err,
                )

    async def _send_temperature_command(self, thermostat_id: str, temp: float, mode: str) -> None:
        """Send temperature command to thermostat with event recording.

        Args:
            thermostat_id: Entity ID of the thermostat
            temp: Temperature to set
            mode: Mode string for logging

        Raises:
            OSError: If there's a network/IO error
            RuntimeError: If there's a service call error
            ValueError: If there's an invalid parameter
        """
        try:
            # Update cache BEFORE service call to prevent false manual override detection
            self._last_set_temperatures[thermostat_id] = temp

            payload = {"entity_id": thermostat_id, ATTR_TEMPERATURE: temp}

            # Record outgoing event
            if self._record_device_event:
                try:
                    self._record_device_event(
                        thermostat_id,
                        "sent",
                        _SERVICE_CLIMATE_SET_TEMPERATURE,
                        {
                            "domain": CLIMATE_DOMAIN,
                            "service": SERVICE_SET_TEMPERATURE,
                            "data": payload,
                        },
                    )
                except (OSError, RuntimeError, ValueError) as err:
                    _LOGGER.debug(
                        "Failed to record sent set_temperature for %s: %s", thermostat_id, err
                    )

            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                payload,
                blocking=True,
            )

            # Record response event
            if self._record_device_event:
                try:
                    self._record_device_event(
                        thermostat_id,
                        "received",
                        _SERVICE_CLIMATE_SET_TEMPERATURE,
                        {"result": "ok"},
                    )
                except (OSError, RuntimeError, ValueError) as err:
                    _LOGGER.debug(
                        "Failed to record received set_temperature for %s: %s", thermostat_id, err
                    )

            _LOGGER.debug(
                "Set thermostat %s to %.1f°C (%s mode)",
                thermostat_id,
                temp,
                mode,
            )

        except (OSError, RuntimeError, ValueError) as err:
            if self._record_device_event:
                try:
                    self._record_device_event(
                        thermostat_id,
                        "received",
                        _SERVICE_CLIMATE_SET_TEMPERATURE,
                        {"result": "error"},
                        status="error",
                        error=str(err),
                    )
                except (OSError, RuntimeError, ValueError) as log_err:
                    _LOGGER.debug(
                        "Failed to record error for set_temperature %s: %s", thermostat_id, log_err
                    )
            _LOGGER.debug(
                "Failed to set temperature for %s to %.1f°C: %s",
                thermostat_id,
                temp,
                err,
            )
            raise

    def _calculate_idle_setpoint(self, area: "Area", target_temp: float) -> float:
        """Calculate desired setpoint for idle state using hysteresis.

        Args:
            area: Area instance
            target_temp: Target temperature

        Returns:
            Desired setpoint for idle state
        """
        hysteresis = self._parse_hysteresis(area)
        current_temp_raw = getattr(area, "current_temperature", None)

        try:
            current_temp = float(current_temp_raw) if current_temp_raw is not None else None
        except (TypeError, ValueError):
            current_temp = None

        desired_setpoint = target_temp
        try:
            rhs = float(target_temp) - float(hysteresis)
        except (TypeError, ValueError):
            rhs = None

        # If current temp is at or above (target - hysteresis) prefer current temp
        if current_temp is not None and rhs is not None and current_temp >= rhs:
            desired_setpoint = current_temp

        _LOGGER.debug(
            "Computed values: current_temp_raw=%s current_temp=%s hysteresis=%s rhs=%s desired_setpoint=%s",
            current_temp_raw,
            current_temp,
            hysteresis,
            rhs,
            desired_setpoint,
        )

        return desired_setpoint

    def _parse_hysteresis(self, area: "Area") -> float:
        """Return a safe hysteresis value for the area (override or default).

        Args:
            area: Area instance

        Returns:
            Hysteresis value as float
        """
        val = getattr(area, "hysteresis_override", None)
        if isinstance(val, (int, float)):
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
        if isinstance(val, str):
            try:
                return float(val)
            except (TypeError, ValueError):
                pass

        am_hyst = getattr(self.area_manager, "hysteresis", None)
        if isinstance(am_hyst, (int, float)):
            try:
                return float(am_hyst)
            except (TypeError, ValueError):
                pass
        if isinstance(am_hyst, str):
            try:
                return float(am_hyst)
            except (TypeError, ValueError):
                pass

        # Fallback default
        return 0.5
