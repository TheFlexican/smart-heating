"""OpenTherm gateway handler for boiler control."""

import asyncio
import logging
from typing import TYPE_CHECKING

from homeassistant.exceptions import HomeAssistantError

from ...exceptions import DeviceError
from .base_device_handler import BaseDeviceHandler

_LOGGER = logging.getLogger(__name__)

# Service constant
SERVICE_OPENTHERM_SET_SETPOINT = "opentherm_gw.set_control_setpoint"


class OpenThermHandler(BaseDeviceHandler):
    """Handle OpenTherm gateway operations."""

    async def async_control_opentherm_gateway(
        self, any_heating: bool, max_target_temp: float
    ) -> None:
        """Control the global OpenTherm gateway based on aggregated demands."""
        gateway_id = self.area_manager.opentherm_gateway_id
        if not gateway_id:
            return

        # Get OpenTherm logger
        from ...const import DOMAIN

        opentherm_logger = self.hass.data.get(DOMAIN, {}).get("opentherm_logger")

        try:
            if any_heating:
                # Collect heating areas (excludes airco areas)
                heating_area_ids, heating_types, overhead_temps = self._collect_heating_areas(
                    opentherm_logger
                )

                # If no non-airco areas need heating, turn off gateway
                if not heating_area_ids:
                    await self._control_gateway_heating_off(gateway_id, opentherm_logger)
                else:
                    # Control boiler for heating
                    await self._control_gateway_heating_on(
                        heating_area_ids,
                        heating_types,
                        overhead_temps,
                        max_target_temp,
                        opentherm_logger,
                    )
            else:
                # Turn off boiler
                await self._control_gateway_heating_off(gateway_id, opentherm_logger)

            # Log modulation status
            self._log_modulation_status(gateway_id, opentherm_logger)

        except (
            HomeAssistantError,
            DeviceError,
            asyncio.TimeoutError,
            AttributeError,
            KeyError,
        ) as err:
            _LOGGER.error("Failed to control OpenTherm gateway %s: %s", gateway_id, err)

    def _collect_heating_areas(self, opentherm_logger):
        heating_area_ids: list[str] = []
        heating_types: dict[str, str] = {}
        overhead_temps: dict[str, float] = {}

        for area_id, area in self.area_manager.get_all_areas().items():
            # Only include non-airco areas in OpenTherm Gateway control
            # Air conditioner areas should bypass boiler/radiator logic
            if area.state == "heating" and area.heating_type != "airco":
                heating_area_ids.append(area_id)
                heating_types[area_id] = area.heating_type

                if area.custom_overhead_temp is not None:
                    overhead_temps[area_id] = area.custom_overhead_temp
                elif area.heating_type == "floor_heating":
                    overhead_temps[area_id] = 10.0
                else:
                    overhead_temps[area_id] = 20.0

                if opentherm_logger and area.current_temperature is not None:
                    opentherm_logger.log_zone_demand(
                        area_id=area_id,
                        area_name=area.name,
                        heating=True,
                        current_temp=area.current_temperature,
                        target_temp=area.target_temperature,
                    )

        return heating_area_ids, heating_types, overhead_temps

    def _calculate_boiler_setpoint(
        self, setpoint_candidates: list[float], max_target_temp: float, overhead: float
    ) -> float:
        if setpoint_candidates:
            return max(setpoint_candidates)
        return max_target_temp + overhead

    def _get_heating_type_counts(self, heating_types: dict) -> tuple[int, int]:
        """Get floor heating and radiator counts from heating types dict."""
        floor_heating_count = sum(1 for ht in heating_types.values() if ht == "floor_heating")
        radiator_count = sum(1 for ht in heating_types.values() if ht == "radiator")
        return floor_heating_count, radiator_count

    def _calculate_pwm_duty(
        self, boiler_setpoint: float, boiler_temp: float, heating_types: dict
    ) -> float:
        """Calculate PWM duty cycle based on boiler temperature."""
        base_offset = 20.0 if any(ht == "floor_heating" for ht in heating_types.values()) else 27.2
        if (boiler_temp - base_offset) == 0:
            return 1.0
        duty = (boiler_setpoint - base_offset) / (boiler_temp - base_offset)
        return min(max(duty, 0.0), 1.0)

    def _apply_pwm_approximation(
        self,
        gateway_device_id: str,
        boiler_setpoint: float,
        heating_types: dict,
    ) -> float:
        """Apply PWM approximation if gateway doesn't support modulation."""
        gateway_state = self.hass.states.get(gateway_device_id)
        if not gateway_state or gateway_state.attributes.get("relative_mod_level"):
            return boiler_setpoint

        boiler_temp_raw = gateway_state.attributes.get("boiler_water_temp")
        if boiler_temp_raw is None:
            boiler_temp_raw = gateway_state.attributes.get("ch_water_temp")

        if boiler_temp_raw is None:
            return boiler_setpoint

        try:
            boiler_temp = float(boiler_temp_raw)
        except (ValueError, TypeError):
            return boiler_setpoint

        duty = self._calculate_pwm_duty(boiler_setpoint, boiler_temp, heating_types)

        if duty < 0.5:
            _LOGGER.debug("PWM approximation: duty=%.2f -> setpoint=0.0", duty)
            return 0.0
        else:
            # Clamp to 0.0 minimum even when duty >= 0.5
            clamped_setpoint = max(0.0, boiler_setpoint)
            _LOGGER.debug(
                "PWM approximation: duty=%.2f -> setpoint=%.1f",
                duty,
                clamped_setpoint,
            )
            return clamped_setpoint

    async def _set_gateway_setpoint(self, gateway_device_id: str, temperature: float) -> None:
        """Set OpenTherm gateway setpoint via service call."""
        try:
            # Clamp temperature to valid range (0.0 - 90.0°C)
            # OpenTherm service enforces: minimum 0.0, maximum 90.0
            clamped_temp = max(0.0, min(90.0, float(temperature)))
            payload = {"gateway_id": gateway_device_id, "temperature": clamped_temp}
            try:
                self._record_device_event(
                    gateway_device_id,
                    "sent",
                    SERVICE_OPENTHERM_SET_SETPOINT,
                    {"domain": "opentherm_gw", "service": "set_control_setpoint", "data": payload},
                )
            except (
                HomeAssistantError,
                DeviceError,
                asyncio.TimeoutError,
                AttributeError,
                KeyError,
            ):
                _LOGGER.debug("Failed to record sent opentherm setpoint for %s", gateway_device_id)

            await self.hass.services.async_call(
                "opentherm_gw",
                "set_control_setpoint",
                payload,
                blocking=False,
            )
            try:
                self._record_device_event(
                    gateway_device_id,
                    "received",
                    SERVICE_OPENTHERM_SET_SETPOINT,
                    {"result": "dispatched"},
                )
            except (
                HomeAssistantError,
                DeviceError,
                asyncio.TimeoutError,
                AttributeError,
                KeyError,
            ):
                _LOGGER.debug(
                    "Failed to record received opentherm setpoint for %s", gateway_device_id
                )
            _LOGGER.info(
                "OpenTherm gateway: Set setpoint via gateway service (gateway_id=%s): %.1f°C",
                gateway_device_id,
                clamped_temp,
            )
        except (
            HomeAssistantError,
            DeviceError,
            asyncio.TimeoutError,
            AttributeError,
            KeyError,
        ) as err:
            _LOGGER.error(
                "Failed to set OpenTherm Gateway setpoint (gateway_id=%s): %s",
                gateway_device_id,
                err,
            )

    def _log_boiler_on(
        self,
        boiler_setpoint: float,
        overhead: float,
        floor_heating_count: int,
        radiator_count: int,
        advanced_enabled: bool,
        heating_curve_enabled: bool,
    ) -> None:
        """Log boiler ON message with appropriate context."""
        if advanced_enabled and heating_curve_enabled:
            _LOGGER.info(
                "OpenTherm gateway: Boiler ON, setpoint=%.1f°C (heating curve, %d floor heating, %d radiator)",
                boiler_setpoint,
                floor_heating_count,
                radiator_count,
            )
        else:
            _LOGGER.info(
                "OpenTherm gateway: Boiler ON, setpoint=%.1f°C (overhead=%.1f°C, %d floor heating, %d radiator)",
                boiler_setpoint,
                overhead,
                floor_heating_count,
                radiator_count,
            )

    async def _control_gateway_heating_on(
        self,
        heating_area_ids: list,
        heating_types: dict,
        overhead_temps: dict,
        max_target_temp: float,
        opentherm_logger,
    ) -> None:
        """Handle gateway control when heating is ON."""
        # Import controller managers
        from ..controllers.heating_curve_manager import compute_area_candidate
        from ..controllers.minimum_setpoint_manager import enforce_minimum_setpoints

        overhead = max(overhead_temps.values()) if overhead_temps else 20.0

        # Advanced control configuration
        advanced_enabled = self.area_manager.advanced_control_enabled
        heating_curve_enabled = self.area_manager.heating_curve_enabled
        pid_enabled = self.area_manager.pid_enabled

        # Collect setpoint candidates per area
        setpoint_candidates = [
            c
            for c in (
                compute_area_candidate(
                    self.hass,
                    self.area_manager,
                    aid,
                    overhead,
                    advanced_enabled,
                    heating_curve_enabled,
                    pid_enabled,
                )
                for aid in heating_area_ids
            )
            if c is not None
        ]

        # Calculate boiler setpoint
        boiler_setpoint = self._calculate_boiler_setpoint(
            setpoint_candidates, max_target_temp, overhead
        )

        # Enforce minimum setpoints
        gateway_device_id = self.area_manager.opentherm_gateway_id
        boiler_setpoint = enforce_minimum_setpoints(
            self.hass, self.area_manager, heating_area_ids, boiler_setpoint, gateway_device_id
        )

        # Get heating type counts
        floor_heating_count, radiator_count = self._get_heating_type_counts(heating_types)

        if not gateway_device_id:
            _LOGGER.error(
                "OpenTherm Gateway ID not configured. "
                "Please set it via Global Settings or service call: smart_heating.set_opentherm_gateway"
            )
            return

        # Apply PWM approximation if needed
        if self.area_manager.pwm_enabled:
            boiler_setpoint = self._apply_pwm_approximation(
                gateway_device_id, boiler_setpoint, heating_types
            )

        # Set gateway setpoint
        await self._set_gateway_setpoint(gateway_device_id, boiler_setpoint)

        # Log boiler control
        self._log_boiler_on(
            boiler_setpoint,
            overhead,
            floor_heating_count,
            radiator_count,
            advanced_enabled,
            heating_curve_enabled,
        )

        # Log with OpenTherm logger
        if opentherm_logger:
            opentherm_logger.log_boiler_control(
                state="ON",
                setpoint=boiler_setpoint,
                heating_areas=heating_area_ids,
                max_target_temp=max_target_temp,
                overhead=overhead,
                floor_heating_count=floor_heating_count,
                radiator_count=radiator_count,
            )

    async def _control_gateway_heating_off(self, gateway_device_id: str, opentherm_logger) -> None:
        """Handle gateway control when heating is OFF."""
        if not gateway_device_id:
            _LOGGER.warning("OpenTherm Gateway ID not configured, cannot turn off")
            return

        try:
            payload = {"gateway_id": gateway_device_id, "temperature": 0.0}
            try:
                self._record_device_event(
                    gateway_device_id,
                    "sent",
                    SERVICE_OPENTHERM_SET_SETPOINT,
                    {"domain": "opentherm_gw", "service": "set_control_setpoint", "data": payload},
                )
            except (
                HomeAssistantError,
                DeviceError,
                asyncio.TimeoutError,
                AttributeError,
                KeyError,
            ):
                _LOGGER.debug(
                    "Failed to record sent opentherm setpoint off for %s", gateway_device_id
                )

            await self.hass.services.async_call(
                "opentherm_gw",
                "set_control_setpoint",
                payload,
                blocking=False,
            )
            try:
                self._record_device_event(
                    gateway_device_id,
                    "received",
                    SERVICE_OPENTHERM_SET_SETPOINT,
                    {"result": "dispatched"},
                )
            except (
                HomeAssistantError,
                DeviceError,
                asyncio.TimeoutError,
                AttributeError,
                KeyError,
            ):
                _LOGGER.debug(
                    "Failed to record received opentherm setpoint off for %s", gateway_device_id
                )
            _LOGGER.info(
                "OpenTherm gateway: Boiler OFF (setpoint=0 via service, gateway_id=%s)",
                gateway_device_id,
            )
        except (
            HomeAssistantError,
            DeviceError,
            asyncio.TimeoutError,
            AttributeError,
            KeyError,
        ) as err:
            _LOGGER.error(
                "Failed to turn off OpenTherm Gateway (gateway_id=%s): %s",
                gateway_device_id,
                err,
            )

        if opentherm_logger:
            opentherm_logger.log_boiler_control(
                state="OFF",
                heating_areas=[],
            )

    def _log_modulation_status(self, gateway_id: str, opentherm_logger) -> None:
        """Log modulation status from gateway state."""
        if not opentherm_logger:
            return

        gateway_state = self.hass.states.get(gateway_id)
        if gateway_state and gateway_state.state != "unavailable":
            attrs = gateway_state.attributes
            opentherm_logger.log_modulation(
                modulation_level=attrs.get("relative_mod_level"),
                flame_on=attrs.get("flame_on"),
                ch_water_temp=attrs.get("ch_water_temp"),
                control_setpoint=attrs.get("control_setpoint"),
                boiler_water_temp=attrs.get("boiler_water_temp"),
            )
