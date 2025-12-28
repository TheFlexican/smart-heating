"""Thermostat device handler."""

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from homeassistant.const import SERVICE_TURN_OFF
from homeassistant.exceptions import HomeAssistantError

from ...const import HVAC_MODE_COOL, HVAC_MODE_HEAT, SUPPORT_TURN_OFF_FLAG
from ...exceptions import DeviceError
from .base_device_handler import BaseDeviceHandler
from .thermostat import (
    HvacController,
    PowerSwitchManager,
    TemperatureSetter,
    ThermostatStateMonitor,
)

if TYPE_CHECKING:
    from ...models import Area

_LOGGER = logging.getLogger(__name__)

# Constant for unknown area name
_UNKNOWN_AREA_NAME = "<unknown>"


class ThermostatHandler(BaseDeviceHandler):
    """Handle thermostat device operations as a coordinator.

    Delegates to specialized components:
    - ThermostatStateMonitor: State monitoring and queries
    - HvacController: HVAC mode management
    - PowerSwitchManager: Power switch operations
    - TemperatureSetter: Temperature setting logic
    """

    def __init__(self, hass, area_manager, capability_detector=None):
        """Initialize thermostat handler."""
        super().__init__(hass, area_manager, capability_detector)

        # Initialize specialized components
        self.state_monitor = ThermostatStateMonitor(hass)
        self.hvac_controller = HvacController(hass, self._record_device_event)
        self.power_switch_manager = PowerSwitchManager(
            hass, self._power_switch_patterns, self._record_device_event
        )
        self.temperature_setter = TemperatureSetter(
            hass,
            area_manager,
            self._is_trv_device,
            self._should_update_temperature,
            self._record_device_event,
        )

    @property
    def _last_set_temperatures(self):
        """Expose temperature setter's cache for backward compatibility with tests."""
        return self.temperature_setter._last_set_temperatures

    @property
    def _last_set_hvac_modes(self):
        """Expose HVAC controller's cache for backward compatibility with tests."""
        return self.hvac_controller._last_set_hvac_modes

    def is_any_thermostat_actively_heating(self, area: "Area") -> bool:
        """Check if any thermostat in the area is actively heating.

        Delegates to ThermostatStateMonitor.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "heating"
        """
        return self.state_monitor.is_any_thermostat_actively_heating(area)

    def is_any_thermostat_actively_cooling(self, area: "Area") -> bool:
        """Check if any thermostat in the area is actively cooling.

        Delegates to ThermostatStateMonitor.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "cooling"
        """
        return self.state_monitor.is_any_thermostat_actively_cooling(area)

    async def async_control_thermostats(
        self,
        area: "Area",
        heating: bool,
        target_temp: Optional[float],
        hvac_mode: str = "heat",
    ) -> None:
        """Control thermostats in an area.

        Coordinates the operation of thermostats by delegating to specialized components.

        Args:
            area: Area to control
            heating: Whether heating/cooling should be active
            target_temp: Target temperature
            hvac_mode: HVAC mode ("heat" or "cool")
        """
        thermostats = area.get_thermostats()

        _LOGGER.debug(
            "async_control_thermostats called: area=%s, heating=%s, target_temp=%s, thermostats=%s",
            getattr(area, "name", _UNKNOWN_AREA_NAME),
            heating,
            target_temp,
            thermostats,
        )

        for thermostat_id in thermostats:
            try:
                _LOGGER.info(
                    "Area %s: Processing thermostat %s (heating=%s target_temp=%s hvac_mode=%s)",
                    getattr(area, "name", _UNKNOWN_AREA_NAME),
                    thermostat_id,
                    heating,
                    target_temp,
                    hvac_mode,
                )
                if heating and target_temp is not None:
                    await self._handle_thermostat_heating(thermostat_id, target_temp, hvac_mode)
                elif target_temp is not None:
                    # Skip hysteresis idle logic for AC/climate areas (hvac_mode != "heat")
                    area_hvac = getattr(area, "hvac_mode", "heat")
                    if area_hvac == "heat":
                        await self._handle_thermostat_idle(area, thermostat_id, target_temp)
                    else:
                        _LOGGER.debug(
                            "Skipping idle hysteresis for AC area %s (hvac_mode=%s)",
                            getattr(area, "name", _UNKNOWN_AREA_NAME),
                            area_hvac,
                        )
                else:
                    await self._handle_thermostat_turn_off(thermostat_id)
            except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
                _LOGGER.error("Failed to control thermostat %s: %s", thermostat_id, err)

    async def _handle_thermostat_heating(
        self, thermostat_id: str, target_temp: float, hvac_mode: str
    ) -> None:
        """Handle thermostat updates when heating/cooling is active.

        Delegates to PowerSwitchManager, HvacController, and TemperatureSetter.

        Args:
            thermostat_id: Entity ID of the thermostat
            target_temp: Target temperature
            hvac_mode: HVAC mode ("heat" or "cool")
        """
        # First, ensure any associated power switch is on
        await self.power_switch_manager.ensure_climate_power_on(thermostat_id)

        # For TRV devices, only temperature setting is needed
        if self._is_trv_device(thermostat_id):
            current_hvac_mode, current_temp = self.state_monitor.get_thermostat_state(thermostat_id)
            await self.temperature_setter.set_temperature_for_heating(
                thermostat_id, target_temp, hvac_mode, current_temp
            )
            return

        # For regular thermostats, set HVAC mode and temperature
        current_hvac_mode, current_temp = self.state_monitor.get_thermostat_state(thermostat_id)

        # Set HVAC mode only if it needs to change
        ha_hvac_mode = HVAC_MODE_HEAT if hvac_mode == "heat" else HVAC_MODE_COOL
        await self.hvac_controller.set_hvac_mode_if_needed(
            thermostat_id, ha_hvac_mode, current_hvac_mode, hvac_mode
        )

        # Set temperature
        await self.temperature_setter.set_temperature_for_heating(
            thermostat_id, target_temp, hvac_mode, current_temp
        )

    async def _handle_thermostat_idle(
        self, area: "Area", thermostat_id: str, target_temp: float
    ) -> None:
        """Handle thermostat updates when area is idle (not actively heating/cooling).

        Delegates to TemperatureSetter.

        Args:
            area: Area instance
            thermostat_id: Entity ID of the thermostat
            target_temp: Target temperature
        """
        await self.temperature_setter.set_temperature_for_idle(area, thermostat_id, target_temp)

    async def _handle_thermostat_turn_off(self, thermostat_id: str) -> None:
        """Turn off thermostat or fall back to minimum setpoint if turn_off not supported.

        Delegates to PowerSwitchManager and TemperatureSetter.

        Args:
            thermostat_id: Entity ID of the thermostat
        """
        # ALWAYS turn off associated power switch first if it exists
        # This is critical for devices like LG ThinQ AC that have separate power switches
        await self.power_switch_manager.turn_off_climate_power(thermostat_id)

        # For TRV devices, set to trv_idle_temp to close valve
        if self._is_trv_device(thermostat_id):
            await self.temperature_setter.set_temperature_for_turn_off(thermostat_id)
            return

        # For non-TRV devices, check if device supports turn_off service
        supported_features = self.state_monitor.get_supported_features(thermostat_id)
        supports_turn_off = (supported_features & SUPPORT_TURN_OFF_FLAG) != 0

        if supports_turn_off:
            try:
                # Use blocking=True so we can catch errors
                from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN

                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_TURN_OFF,
                    {"entity_id": thermostat_id},
                    blocking=True,
                )
                _LOGGER.debug("Turned off thermostat %s", thermostat_id)
                return
            except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
                _LOGGER.debug(
                    "Failed to turn off thermostat %s: %s, falling back to min temp",
                    thermostat_id,
                    err,
                )

        # Fall back to temperature setting if turn_off not supported
        await self.temperature_setter.set_temperature_for_turn_off(thermostat_id)
