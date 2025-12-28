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

# Service and message constants
SERVICE_SWITCH_TURN_ON = "switch.turn_on"
_SERVICE_SWITCH_TURN_OFF = "switch.turn_off"
MSG_SWITCH_CONTROL_FAILED = "Failed to control switch %s: %s"


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

        Args:
            area: Area instance

        Returns:
            True if any thermostat is actively heating
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

    def _should_keep_switch_on_when_heating_stops(
        self, area: "Area", thermostats_still_heating: bool
    ) -> bool:
        """Determine if switch should stay on when heating stops.

        Args:
            area: Area instance
            thermostats_still_heating: Whether thermostats are still actively heating

        Returns:
            True if switch should remain on, False otherwise
        """
        if not thermostats_still_heating:
            return False

        area_state = getattr(area, "state", None)
        manual_override = getattr(area, "manual_override", False)

        return area_state == "heating" or manual_override

    def _safe_record_device_event(
        self, switch_id: str, event_type: str, service: str, data: dict
    ) -> None:
        """Safely record device event with error handling.

        Args:
            switch_id: Switch entity ID
            event_type: Event type (sent/received)
            service: Service name
            data: Event data
        """
        try:
            self._record_device_event(switch_id, event_type, service, data)
        except (AttributeError, KeyError, TypeError, ValueError) as err:
            _LOGGER.debug("Failed to record %s event for %s: %s", event_type, switch_id, err)

    def _get_switch_state(self, switch_id: str) -> str | None:
        """Get current state of a switch.

        Args:
            switch_id: Switch entity ID

        Returns:
            Current state or None
        """
        current = self.hass.states.get(switch_id)
        return getattr(current, "state", None)

    async def _turn_on_switch(self, switch_id: str) -> None:
        """Turn on a switch with event recording.

        Args:
            switch_id: Switch entity ID
        """
        current_state = self._get_switch_state(switch_id)
        if current_state == "on":
            return

        payload = {"entity_id": switch_id}
        self._safe_record_device_event(
            switch_id,
            "sent",
            SERVICE_SWITCH_TURN_ON,
            {"domain": "switch", "service": SERVICE_TURN_ON, "data": payload},
        )

        await self.hass.services.async_call("switch", SERVICE_TURN_ON, payload, blocking=False)

        self._safe_record_device_event(
            switch_id, "received", SERVICE_SWITCH_TURN_ON, {"result": "dispatched"}
        )

    async def _turn_off_switch(self, switch_id: str) -> None:
        """Turn off a switch with event recording.

        Args:
            switch_id: Switch entity ID
        """
        current_state = self._get_switch_state(switch_id)
        if current_state == "off":
            return

        payload = {"entity_id": switch_id}
        self._safe_record_device_event(
            switch_id,
            "sent",
            _SERVICE_SWITCH_TURN_OFF,
            {"domain": "switch", "service": SERVICE_TURN_OFF, "data": payload},
        )

        await self.hass.services.async_call("switch", SERVICE_TURN_OFF, payload, blocking=False)

        self._safe_record_device_event(
            switch_id, "received", _SERVICE_SWITCH_TURN_OFF, {"result": "dispatched"}
        )
        _LOGGER.debug("Turned off switch %s", switch_id)

    async def _handle_heating_mode(self, switch_id: str) -> None:
        """Handle switch control when heating is requested.

        Args:
            switch_id: Switch entity ID
        """
        try:
            await self._turn_on_switch(switch_id)
        except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
            _LOGGER.error(MSG_SWITCH_CONTROL_FAILED, switch_id, err, exc_info=True)

    async def _handle_idle_mode(
        self, switch_id: str, area: "Area", thermostats_still_heating: bool
    ) -> None:
        """Handle switch control when heating should stop.

        Args:
            switch_id: Switch entity ID
            area: Area instance
            thermostats_still_heating: Whether thermostats are still actively heating
        """
        if self._should_keep_switch_on_when_heating_stops(area, thermostats_still_heating):
            _LOGGER.info(
                "Area %s: Target reached but thermostat still heating - keeping switch %s ON",
                area.area_id,
                switch_id,
            )
            try:
                await self._turn_on_switch(switch_id)
            except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
                _LOGGER.error(MSG_SWITCH_CONTROL_FAILED, switch_id, err, exc_info=True)
            return

        if not getattr(area, "shutdown_switches_when_idle", True):
            _LOGGER.debug("Keeping switch %s on (shutdown_switches_when_idle=False)", switch_id)
            return

        try:
            await self._turn_off_switch(switch_id)
        except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
            _LOGGER.error(MSG_SWITCH_CONTROL_FAILED, switch_id, err, exc_info=True)

    async def async_control_switches(self, area: "Area", heating: bool) -> None:
        """Control switches (pumps, relays) in an area.

        Args:
            area: Area instance
            heating: True to turn on heating, False to turn off
        """
        switches = area.get_switches()
        thermostats_still_heating = self._check_thermostats_actively_heating(area)

        for switch_id in switches:
            try:
                if heating:
                    await self._handle_heating_mode(switch_id)
                else:
                    await self._handle_idle_mode(switch_id, area, thermostats_still_heating)
            except (HomeAssistantError, DeviceError, asyncio.TimeoutError, AttributeError) as err:
                _LOGGER.error(MSG_SWITCH_CONTROL_FAILED, switch_id, err, exc_info=True)
