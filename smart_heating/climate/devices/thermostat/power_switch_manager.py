"""Power switch manager component for climate devices."""

import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Optional

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.const import SERVICE_TURN_ON
from homeassistant.exceptions import HomeAssistantError

from ....exceptions import DeviceError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class PowerSwitchManager:
    """Manage power switches for climate devices."""

    def __init__(
        self,
        hass: "HomeAssistant",
        power_switch_patterns_func: Callable[[str], list[str]],
        record_device_event: Optional[Callable] = None,
    ):
        """Initialize power switch manager.

        Args:
            hass: Home Assistant instance
            power_switch_patterns_func: Function to get power switch patterns for a base name
            record_device_event: Optional callback to record device events
        """
        self.hass = hass
        self._power_switch_patterns = power_switch_patterns_func
        self._record_device_event = record_device_event

    async def turn_on_switch_and_wait(self, switch_id: str, climate_entity_id: str) -> bool:
        """Turn on a power switch and wait for it to report 'on'.

        Args:
            switch_id: Entity ID of the switch
            climate_entity_id: Entity ID of the associated climate device

        Returns:
            True if the switch is or becomes 'on' within the timeout window
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
                    if self._record_device_event:
                        try:
                            self._record_device_event(
                                switch_id,
                                "sent",
                                "switch.turn_on",
                                {"domain": "switch", "service": "turn_on", "data": payload},
                            )
                        except (OSError, RuntimeError, ValueError) as err:
                            _LOGGER.debug(
                                "Failed to record sent event for switch %s: %s", switch_id, err
                            )

                    await self.hass.services.async_call(
                        "switch",
                        "turn_on",
                        payload,
                        blocking=False,
                    )
                except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
                    _LOGGER.debug("Failed to call turn_on for switch %s: %s", switch_id, err)

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
        except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Error while turning on switch %s: %s", switch_id, err)
            return False

    async def ensure_climate_power_on(self, climate_entity_id: str) -> None:
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
        for switch_id in self._power_switch_patterns(base_name):
            state = self.hass.states.get(switch_id)
            if state:
                # Found a power switch, ensure it's on
                success = await self.turn_on_switch_and_wait(switch_id, climate_entity_id)
                if not success:
                    _LOGGER.debug("Power switch %s did not become 'on' within timeout", switch_id)
                return  # Found and handled the switch

        # No power switch found, which is normal for most thermostats
        _LOGGER.debug("No power switch found for %s", climate_entity_id)

        # As a fallback, some climate integrations require calling the
        # climate.turn_on service (no separate switch). Try to turn the
        # climate entity itself on if it is currently off.
        await self._try_turn_on_climate_entity(climate_entity_id)

    async def _try_turn_on_climate_entity(self, climate_entity_id: str) -> None:
        """Try to turn on climate entity directly if it's off.

        Args:
            climate_entity_id: Climate entity ID
        """
        try:
            state = self.hass.states.get(climate_entity_id)
            if state and getattr(state, "state", None) != "on":
                _LOGGER.info("Turning on climate entity %s", climate_entity_id)
                try:
                    payload = {"entity_id": climate_entity_id}
                    if self._record_device_event:
                        try:
                            self._record_device_event(
                                climate_entity_id,
                                "sent",
                                "climate.turn_on",
                                {
                                    "domain": CLIMATE_DOMAIN,
                                    "service": SERVICE_TURN_ON,
                                    "data": payload,
                                },
                            )
                        except (OSError, RuntimeError, ValueError) as err:
                            _LOGGER.debug(
                                "Failed to record sent turn_on for %s: %s", climate_entity_id, err
                            )

                    await self.hass.services.async_call(
                        CLIMATE_DOMAIN,
                        SERVICE_TURN_ON,
                        payload,
                        blocking=False,
                    )
                    if self._record_device_event:
                        try:
                            self._record_device_event(
                                climate_entity_id,
                                "received",
                                "climate.turn_on",
                                {"result": "dispatched"},
                            )
                        except (OSError, RuntimeError, ValueError) as err:
                            _LOGGER.debug(
                                "Failed to record received turn_on for %s: %s",
                                climate_entity_id,
                                err,
                            )
                except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
                    # Be defensive - do not raise from best-effort fallback
                    _LOGGER.debug(
                        "Failed to turn on climate entity %s (fallback): %s", climate_entity_id, err
                    )
        except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
            # Be defensive - do not raise from best-effort fallback
            _LOGGER.debug(
                "Failed to turn on climate entity %s (fallback): %s", climate_entity_id, err
            )

    async def turn_off_climate_power(self, climate_entity_id: str) -> None:
        """Turn off climate device power switch if it exists.

        Args:
            climate_entity_id: Climate entity ID
        """
        # Extract base name from climate entity
        if "." not in climate_entity_id:
            return

        base_name = climate_entity_id.split(".", 1)[1]

        # Check for common power switch patterns
        for switch_id in self._power_switch_patterns(base_name):
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
                        if self._record_device_event:
                            try:
                                self._record_device_event(
                                    switch_id,
                                    "sent",
                                    "switch.turn_off",
                                    {"domain": "switch", "service": "turn_off", "data": payload},
                                )
                            except (OSError, RuntimeError, ValueError) as err:
                                _LOGGER.debug(
                                    "Failed to record sent turn_off for %s: %s", switch_id, err
                                )

                        await self.hass.services.async_call(
                            "switch",
                            "turn_off",
                            payload,
                            blocking=False,
                        )
                    except (HomeAssistantError, DeviceError, asyncio.TimeoutError) as err:
                        # Some integrations reject redundant off commands - ignore
                        if self._record_device_event:
                            try:
                                self._record_device_event(
                                    switch_id,
                                    "received",
                                    "switch.turn_off",
                                    {"result": "error"},
                                    status="error",
                                    error=str(err),
                                )
                            except (OSError, RuntimeError, ValueError) as log_err:
                                _LOGGER.debug(
                                    "Failed to record received error for turn_off %s: %s",
                                    switch_id,
                                    log_err,
                                )
                        _LOGGER.debug(
                            "Failed to turn off switch %s (may already be off): %s",
                            switch_id,
                            err,
                        )
                else:
                    _LOGGER.debug("Power switch %s already off", switch_id)
                return  # Found and handled the switch
