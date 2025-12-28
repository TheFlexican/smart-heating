"""Switch device handler for heating/cooling control."""

import asyncio
import logging
from typing import TYPE_CHECKING

from homeassistant.const import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.exceptions import HomeAssistantError

from ...exceptions import DeviceError
from .base_device_handler import BaseDeviceHandler

if TYPE_CHECKING:
    from ...models import Area

_LOGGER = logging.getLogger(__name__)

# Constants for duplicated strings
_SERVICE_SWITCH_TURN_ON = "switch.turn_on"
_SERVICE_SWITCH_TURN_OFF = "switch.turn_off"
_MSG_SWITCH_CONTROL_FAILED = "Failed to control switch %s: %s"


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

    def _record_switch_event_safe(
        self, switch_id: str, direction: str, service: str, data: dict
    ) -> None:
        """Record switch event, suppressing errors."""
        try:
            self._record_device_event(switch_id, direction, service, data)
        except (AttributeError, KeyError, TypeError, ValueError) as err:
            _LOGGER.debug("Failed to record %s %s for %s: %s", direction, service, switch_id, err)

    async def _turn_switch_on(self, switch_id: str) -> bool:
        """Turn on a switch if not already on. Returns True if action taken."""
        current = self.hass.states.get(switch_id)
        if getattr(current, "state", None) == "on":
            return False

        payload = {"entity_id": switch_id}
        self._record_switch_event_safe(
            switch_id,
            "sent",
            _SERVICE_SWITCH_TURN_ON,
            {"domain": "switch", "service": SERVICE_TURN_ON, "data": payload},
        )

        await self.hass.services.async_call("switch", SERVICE_TURN_ON, payload, blocking=False)

        self._record_switch_event_safe(
            switch_id, "received", _SERVICE_SWITCH_TURN_ON, {"result": "dispatched"}
        )
        return True

    async def _turn_switch_off(self, switch_id: str) -> bool:
        """Turn off a switch if not already off. Returns True if action taken."""
        current = self.hass.states.get(switch_id)
        if getattr(current, "state", None) == "off":
            return False

        payload = {"entity_id": switch_id}
        self._record_switch_event_safe(
            switch_id,
            "sent",
            _SERVICE_SWITCH_TURN_OFF,
            {"domain": "switch", "service": SERVICE_TURN_OFF, "data": payload},
        )

        await self.hass.services.async_call("switch", SERVICE_TURN_OFF, payload, blocking=False)

        self._record_switch_event_safe(
            switch_id, "received", _SERVICE_SWITCH_TURN_OFF, {"result": "dispatched"}
        )
        _LOGGER.debug("Turned off switch %s", switch_id)
        return True

    def _should_keep_switch_on(self, area: "Area", thermostats_still_heating: bool) -> bool:
        """Determine if switch should stay on when not actively heating."""
        if not thermostats_still_heating:
            return False
        return getattr(area, "state", None) == "heating" or getattr(area, "manual_override", False)

    async def _control_single_switch(
        self, switch_id: str, area: "Area", heating: bool, thermostats_still_heating: bool
    ) -> None:
        """Control a single switch based on heating state."""
        try:
            if heating:
                await self._turn_switch_on(switch_id)
                return

            # Not actively heating - determine action
            if self._should_keep_switch_on(area, thermostats_still_heating):
                _LOGGER.info(
                    "Area %s: Target reached but thermostat still heating - keeping switch %s ON",
                    area.area_id,
                    switch_id,
                )
                await self._turn_switch_on(switch_id)
            elif getattr(area, "shutdown_switches_when_idle", True):
                await self._turn_switch_off(switch_id)
            else:
                _LOGGER.debug("Keeping switch %s on (shutdown_switches_when_idle=False)", switch_id)
        except (HomeAssistantError, DeviceError, asyncio.TimeoutError, AttributeError) as err:
            _LOGGER.error(_MSG_SWITCH_CONTROL_FAILED, switch_id, err, exc_info=True)

    async def async_control_switches(self, area: "Area", heating: bool) -> None:
        """Control switches (pumps, relays) in an area."""
        switches = area.get_switches()
        thermostats_still_heating = self._check_thermostats_actively_heating(area)

        for switch_id in switches:
            await self._control_single_switch(switch_id, area, heating, thermostats_still_heating)
