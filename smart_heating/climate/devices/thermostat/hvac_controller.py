"""HVAC mode controller component."""

import logging
from typing import TYPE_CHECKING, Callable, Optional

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class HvacController:
    """Control HVAC modes for thermostats."""

    def __init__(
        self,
        hass: "HomeAssistant",
        record_device_event: Optional[Callable] = None,
    ):
        """Initialize HVAC controller.

        Args:
            hass: Home Assistant instance
            record_device_event: Optional callback to record device events
        """
        self.hass = hass
        self._record_device_event = record_device_event
        self._last_set_hvac_modes: dict[str, str] = {}

    async def set_hvac_mode_if_needed(
        self,
        thermostat_id: str,
        desired_mode: str,
        current_mode: Optional[str],
        hvac_mode_str: str,
    ) -> None:
        """Set HVAC mode if it differs from the current mode (best-effort).

        Uses the current device state as the authoritative source. A cache is used
        as a fallback when device state is unknown/unavailable to avoid sending
        redundant HVAC mode commands.

        If the device reports a different mode than desired, we always send the
        command to ensure external changes are overridden.

        Args:
            thermostat_id: Entity ID of the thermostat
            desired_mode: Desired HVAC mode
            current_mode: Current HVAC mode from device state
            hvac_mode_str: Human-readable HVAC mode string for logging
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
        await self._send_hvac_mode_command(thermostat_id, desired_mode, hvac_mode_str)

    async def _send_hvac_mode_command(
        self, thermostat_id: str, desired_mode: str, hvac_mode_str: str
    ) -> None:
        """Send HVAC mode command to thermostat.

        Args:
            thermostat_id: Entity ID of the thermostat
            desired_mode: Desired HVAC mode
            hvac_mode_str: Human-readable HVAC mode string for logging
        """
        try:
            self._last_set_hvac_modes[thermostat_id] = desired_mode
            payload = {"entity_id": thermostat_id, "hvac_mode": desired_mode}

            # Record outgoing event
            if self._record_device_event:
                try:
                    self._record_device_event(
                        thermostat_id,
                        "sent",
                        "climate.set_hvac_mode",
                        {"domain": CLIMATE_DOMAIN, "service": "set_hvac_mode", "data": payload},
                    )
                except (OSError, RuntimeError, ValueError) as err:
                    _LOGGER.debug(
                        "Failed to record sent hvac_mode event for %s: %s", thermostat_id, err
                    )

            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                "set_hvac_mode",
                payload,
                blocking=False,
            )

            # Record response event
            if self._record_device_event:
                try:
                    self._record_device_event(
                        thermostat_id,
                        "received",
                        "climate.set_hvac_mode",
                        {"result": "dispatched"},
                    )
                except (OSError, RuntimeError, ValueError) as err:
                    _LOGGER.debug(
                        "Failed to record received hvac_mode event for %s: %s", thermostat_id, err
                    )

            _LOGGER.debug("Set thermostat %s to %s mode", thermostat_id, hvac_mode_str)

        except (OSError, RuntimeError, ValueError) as err:
            _LOGGER.debug(
                "Failed to set hvac_mode for %s (may already be in target mode): %s",
                thermostat_id,
                err,
            )
