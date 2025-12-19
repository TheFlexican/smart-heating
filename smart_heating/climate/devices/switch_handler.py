"""Switch device handler for heating/cooling control."""

import logging
from typing import TYPE_CHECKING

from homeassistant.const import SERVICE_TURN_OFF, SERVICE_TURN_ON

from .base_device_handler import BaseDeviceHandler

if TYPE_CHECKING:
    from ...models import Area

_LOGGER = logging.getLogger(__name__)


class SwitchHandler(BaseDeviceHandler):
    """Handle switch (pumps, relays) device operations."""

    def __init__(
        self,
        hass,
        area_manager,
        capability_detector=None,
        thermostat_handler=None,
        parent_handler=None,
    ):
        """Initialize switch handler.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            capability_detector: Device capability detector (optional)
            thermostat_handler: Shared thermostat handler instance (optional)
            parent_handler: Parent DeviceControlHandler for delegation (optional)
        """
        super().__init__(hass, area_manager, capability_detector)
        self._thermostat_handler = thermostat_handler
        self._parent_handler = parent_handler

    def _check_thermostats_actively_heating(self, area: "Area") -> bool:
        """Check if any thermostat is actively heating.

        This method can be overridden for testing or delegates to parent if available.
        """
        # If used through orchestrator, delegate to it (supports test mocking)
        if self._parent_handler and hasattr(
            self._parent_handler, "is_any_thermostat_actively_heating"
        ):
            return self._parent_handler.is_any_thermostat_actively_heating(area)

        # Otherwise use thermostat handler directly
        if self._thermostat_handler:
            return self._thermostat_handler.is_any_thermostat_actively_heating(area)

        # Fallback: create temporary handler if not provided
        from .thermostat_handler import ThermostatHandler

        temp_handler = ThermostatHandler(self.hass, self.area_manager, self.capability_detector)
        return temp_handler.is_any_thermostat_actively_heating(area)

    async def async_control_switches(self, area: "Area", heating: bool) -> None:
        """Control switches (pumps, relays) in an area."""
        switches = area.get_switches()

        # Check if any thermostat is still actively heating
        thermostats_still_heating = self._check_thermostats_actively_heating(area)

        for switch_id in switches:
            try:
                if heating:
                    await self.hass.services.async_call(
                        "switch",
                        SERVICE_TURN_ON,
                        {"entity_id": switch_id},
                        blocking=False,
                    )
                    _LOGGER.debug("Turned on switch %s", switch_id)
                else:
                    # When stopping heating we should only keep switches on if the
                    # thermostat still reports it is heating AND the area is still
                    # considered to be in a heating state. This avoids re-enabling
                    # pumps when there are no active heating events for the area
                    # (e.g., stale thermostat hvac_action values).
                    if thermostats_still_heating and (
                        getattr(area, "state", None) == "heating"
                        or getattr(area, "manual_override", False)
                    ):
                        _LOGGER.info(
                            "Area %s: Target reached but thermostat still heating - keeping switch %s ON",
                            area.area_id,
                            switch_id,
                        )
                        await self.hass.services.async_call(
                            "switch",
                            SERVICE_TURN_ON,
                            {"entity_id": switch_id},
                            blocking=False,
                        )
                    elif getattr(area, "shutdown_switches_when_idle", True):
                        await self.hass.services.async_call(
                            "switch",
                            SERVICE_TURN_OFF,
                            {"entity_id": switch_id},
                            blocking=False,
                        )
                        _LOGGER.debug("Turned off switch %s", switch_id)
                    else:
                        _LOGGER.debug(
                            "Keeping switch %s on (shutdown_switches_when_idle=False)",
                            switch_id,
                        )
            except Exception as err:
                _LOGGER.error("Failed to control switch %s: %s", switch_id, err)
