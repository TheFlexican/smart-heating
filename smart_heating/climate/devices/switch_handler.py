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
                    try:
                        # Only call turn_on if the switch is not already on to avoid
                        # repeated service calls when state is unchanged.
                        current = self.hass.states.get(switch_id)
                        current_state = getattr(current, "state", None)
                        if current_state != "on":
                            payload = {"entity_id": switch_id}
                            try:
                                self._record_device_event(
                                    switch_id,
                                    "sent",
                                    "switch.turn_on",
                                    {
                                        "domain": "switch",
                                        "service": SERVICE_TURN_ON,
                                        "data": payload,
                                    },
                                )
                            except Exception:
                                _LOGGER.debug("Failed to record sent turn_on for %s", switch_id)

                            await self.hass.services.async_call(
                                "switch",
                                SERVICE_TURN_ON,
                                payload,
                                blocking=False,
                            )
                            try:
                                self._record_device_event(
                                    switch_id,
                                    "received",
                                    "switch.turn_on",
                                    {"result": "dispatched"},
                                )
                            except Exception:
                                _LOGGER.debug("Failed to record received turn_on for %s", switch_id)
                    except Exception as err:
                        _LOGGER.error("Failed to control switch %s: %s", switch_id, err)
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
                        try:
                            # Only call turn_on if the switch is not already on
                            current = self.hass.states.get(switch_id)
                            current_state = getattr(current, "state", None)
                            if current_state != "on":
                                payload = {"entity_id": switch_id}
                                try:
                                    self._record_device_event(
                                        switch_id,
                                        "sent",
                                        "switch.turn_on",
                                        {
                                            "domain": "switch",
                                            "service": SERVICE_TURN_ON,
                                            "data": payload,
                                        },
                                    )
                                except Exception:
                                    _LOGGER.debug("Failed to record sent turn_on for %s", switch_id)

                                await self.hass.services.async_call(
                                    "switch",
                                    SERVICE_TURN_ON,
                                    payload,
                                    blocking=False,
                                )
                                try:
                                    self._record_device_event(
                                        switch_id,
                                        "received",
                                        "switch.turn_on",
                                        {"result": "dispatched"},
                                    )
                                except Exception:
                                    _LOGGER.debug(
                                        "Failed to record received turn_on for %s", switch_id
                                    )
                        except Exception as err:
                            _LOGGER.error("Failed to control switch %s: %s", switch_id, err)
                    elif getattr(area, "shutdown_switches_when_idle", True):
                        try:
                            # Only call turn_off if the switch is not already off
                            current = self.hass.states.get(switch_id)
                            current_state = getattr(current, "state", None)
                            if current_state != "off":
                                payload = {"entity_id": switch_id}
                                try:
                                    self._record_device_event(
                                        switch_id,
                                        "sent",
                                        "switch.turn_off",
                                        {
                                            "domain": "switch",
                                            "service": SERVICE_TURN_OFF,
                                            "data": payload,
                                        },
                                    )
                                except Exception:
                                    _LOGGER.debug(
                                        "Failed to record sent turn_off for %s", switch_id
                                    )

                                await self.hass.services.async_call(
                                    "switch",
                                    SERVICE_TURN_OFF,
                                    payload,
                                    blocking=False,
                                )
                                try:
                                    self._record_device_event(
                                        switch_id,
                                        "received",
                                        "switch.turn_off",
                                        {"result": "dispatched"},
                                    )
                                except Exception:
                                    _LOGGER.debug(
                                        "Failed to record received turn_off for %s", switch_id
                                    )
                                _LOGGER.debug("Turned off switch %s", switch_id)
                        except Exception as err:
                            _LOGGER.error("Failed to control switch %s: %s", switch_id, err)
                    else:
                        _LOGGER.debug(
                            "Keeping switch %s on (shutdown_switches_when_idle=False)",
                            switch_id,
                        )
            except Exception as err:
                _LOGGER.error("Failed to control switch %s: %s", switch_id, err)
