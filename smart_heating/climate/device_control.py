"""Device control orchestrator for climate system.

This module acts as an orchestrator, delegating to specialized handlers for:
- Thermostats (TRVs, smart thermostats, AC units)
- Switches (pumps, relays)
- Valves (position-based, temperature-based)
- OpenTherm gateway (boiler control)
"""

import logging
from typing import Optional

from homeassistant.core import HomeAssistant

from ..core.area_manager import AreaManager
from ..models import Area
from .devices import (
    OpenThermHandler,
    SwitchHandler,
    ThermostatHandler,
    ValveHandler,
)

_LOGGER = logging.getLogger(__name__)


class DeviceControlHandler:
    """Handle device control operations (thermostats, switches, valves).

    This is an orchestrator that delegates to specialized handlers.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        area_manager: AreaManager,
        capability_detector=None,
    ):
        """Initialize device control handler.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            capability_detector: DeviceCapabilityDetector instance (optional)
        """
        self.hass = hass
        self.area_manager = area_manager
        self.capability_detector = capability_detector

        # Initialize specialized handlers
        self.thermostat_handler = ThermostatHandler(hass, area_manager, capability_detector)
        self.switch_handler = SwitchHandler(
            hass, area_manager, capability_detector, self.thermostat_handler, parent_handler=self
        )
        self.valve_handler = ValveHandler(hass, area_manager, capability_detector)
        self.opentherm_handler = OpenThermHandler(hass, area_manager, capability_detector)

    # === Thermostat Operations (delegated) ===

    def is_any_thermostat_actively_heating(self, area: Area) -> bool:
        """Check if any thermostat in the area is actively heating.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "heating"
        """
        return self.thermostat_handler.is_any_thermostat_actively_heating(area)

    def is_any_thermostat_actively_cooling(self, area: Area) -> bool:
        """Check if any thermostat in the area is actively cooling.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "cooling"
        """
        return self.thermostat_handler.is_any_thermostat_actively_cooling(area)

    async def async_control_thermostats(
        self,
        area: Area,
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
        await self.thermostat_handler.async_control_thermostats(
            area, heating, target_temp, hvac_mode
        )

    # === Switch Operations (delegated) ===

    async def async_control_switches(self, area: Area, heating: bool) -> None:
        """Control switches (pumps, relays) in an area.

        Args:
            area: Area to control
            heating: Whether heating should be active
        """
        await self.switch_handler.async_control_switches(area, heating)

    # === Valve Operations (delegated) ===

    def get_valve_capability(self, entity_id: str):
        """Get valve control capabilities from HA entity.

        Args:
            entity_id: Entity ID of the valve

        Returns:
            Dict with capability information
        """
        return self.valve_handler.get_valve_capability(entity_id)

    async def async_control_valves(
        self, area: Area, heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control valves/TRVs in an area.

        Args:
            area: Area to control
            heating: Whether heating should be active
            target_temp: Target temperature
        """
        await self.valve_handler.async_control_valves(area, heating, target_temp)

    async def async_set_valves_to_off(self, area: Area, off_temperature: float = 0.0) -> None:
        """Set all valves in an area to an "off" state.

        Args:
            area: Area to control
            off_temperature: Temperature to set for temperature-controlled valves
        """
        await self.valve_handler.async_set_valves_to_off(area, off_temperature)

    # === OpenTherm Gateway Operations (delegated) ===

    async def async_control_opentherm_gateway(
        self, any_heating: bool, max_target_temp: float
    ) -> None:
        """Control the global OpenTherm gateway based on aggregated demands.

        Args:
            any_heating: Whether any area needs heating
            max_target_temp: Maximum target temperature across all heating areas
        """
        await self.opentherm_handler.async_control_opentherm_gateway(any_heating, max_target_temp)

    # === Utility Methods ===

    def _is_trv_device(self, entity_id: str) -> bool:
        """Detect if a climate entity is a TRV.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if entity appears to be a TRV device
        """
        return self.thermostat_handler._is_trv_device(entity_id)

    def _get_thermostat_state(self, thermostat_id: str):
        """Return (hvac_mode, temperature) for a thermostat if available.

        Args:
            thermostat_id: Thermostat entity ID

        Returns:
            Tuple of (hvac_mode, temperature)
        """
        return self.thermostat_handler._get_thermostat_state(thermostat_id)

    def _should_update_temperature(
        self, current_temp: Optional[float], last_temp: Optional[float], target_temp: float
    ) -> bool:
        """Return True when temperature should be updated.

        Args:
            current_temp: Current temperature from device
            last_temp: Last set temperature from cache
            target_temp: Target temperature to set

        Returns:
            True if temperature should be updated
        """
        return self.thermostat_handler._should_update_temperature(
            current_temp, last_temp, target_temp
        )

    # === Additional exposed methods for testing ===

    def _parse_hysteresis(self, area):
        """Parse hysteresis value from area (delegated to thermostat handler)."""
        return self.thermostat_handler.temperature_setter._parse_hysteresis(area)

    async def _handle_thermostat_idle(self, area, thermostat_id: str, target_temp: float):
        """Handle thermostat idle state (delegated to thermostat handler)."""
        await self.thermostat_handler._handle_thermostat_idle(area, thermostat_id, target_temp)

    async def _handle_thermostat_turn_off(self, thermostat_id: str):
        """Turn off thermostat (delegates to thermostat handler).

        This orchestrator method delegates to the specialized handler to maintain
        a single source of truth and avoid code duplication.
        """
        await self.thermostat_handler._handle_thermostat_turn_off(thermostat_id)

    async def _handle_thermostat_heating(
        self, thermostat_id: str, target_temp: float, hvac_mode: str
    ):
        """Handle thermostat heating (delegated to thermostat handler)."""
        await self.thermostat_handler._handle_thermostat_heating(
            thermostat_id, target_temp, hvac_mode
        )

    async def _async_ensure_climate_power_on(self, climate_entity_id: str):
        """Ensure climate power is on (delegated to thermostat handler's power switch manager)."""
        await self.thermostat_handler.power_switch_manager.ensure_climate_power_on(
            climate_entity_id
        )

    async def _async_turn_off_climate_power(self, climate_entity_id: str):
        """Turn off climate power (delegated to thermostat handler's power switch manager)."""
        await self.thermostat_handler.power_switch_manager.turn_off_climate_power(climate_entity_id)

    def _collect_heating_areas(self, opentherm_logger):
        """Collect heating areas (delegated to opentherm handler)."""
        return self.opentherm_handler._collect_heating_areas(opentherm_logger)

    def _compute_area_candidate(
        self,
        area_id: str,
        overhead: float,
        advanced_enabled: bool,
        heating_curve_enabled: bool,
    ):
        """Compute area candidate setpoint (delegates to heating curve manager).

        This orchestrator method delegates to the controller manager to maintain
        a single source of truth and avoid code duplication.
        """
        from .controllers.heating_curve_manager import compute_area_candidate

        return compute_area_candidate(
            self.hass,
            self.area_manager,
            area_id,
            overhead,
            advanced_enabled,
            heating_curve_enabled,
        )

    def _enforce_minimum_setpoints(
        self, heating_area_ids: list[str], boiler_setpoint: float, gateway_device_id: str
    ) -> float:
        """Enforce minimum setpoints (delegated to controller manager)."""
        from .controllers.minimum_setpoint_manager import enforce_minimum_setpoints

        return enforce_minimum_setpoints(
            self.hass, self.area_manager, heating_area_ids, boiler_setpoint, gateway_device_id
        )

    def _apply_heating_curve(
        self,
        area_id: str,
        candidate: float,
        outside_temp,
        advanced_enabled: bool,
        heating_curve_enabled: bool,
    ):
        """Apply heating curve (delegated to controller manager)."""
        from .controllers.heating_curve_manager import _apply_heating_curve

        return _apply_heating_curve(
            self.area_manager,
            area_id,
            candidate,
            outside_temp,
            advanced_enabled,
            heating_curve_enabled,
        )

    def _apply_pid_adjustment(self, area_id: str, candidate: float):
        """Apply PID adjustment (delegated to controller manager)."""
        from .controllers.pid_controller_manager import apply_pid_adjustment

        return apply_pid_adjustment(self.area_manager, area_id, candidate)
