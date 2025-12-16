"""Diagnostic service handlers for Smart Heating."""

import asyncio
import logging
from typing import Any

from homeassistant.core import ServiceCall

from ..area_manager import AreaManager
from ..coordinator import SmartHeatingCoordinator
from ..const import ATTR_AREA_ID, ATTR_HVAC_MODE, ATTR_TEMPERATURE

_LOGGER = logging.getLogger(__name__)


async def async_handle_force_thermostat_update(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Force thermostat sequence for debugging.

    Steps (per thermostat):
    1. Turn on any associated power switch if exists and wait for it to report 'on'.
    2. If climate entity state is not 'on', call climate.turn_on as fallback.
    3. Set HVAC mode (if provided) and set temperature (if provided).

    This is a best-effort diagnostic helper intended to be run interactively.
    """
    data: dict[str, Any] = call.data
    area_id = data.get(ATTR_AREA_ID)
    target_temp = data.get(ATTR_TEMPERATURE)
    hvac_mode = data.get(ATTR_HVAC_MODE)

    if not area_id:
        _LOGGER.error("force_thermostat_update: area_id missing")
        return

    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error("force_thermostat_update: area %s not found", area_id)
        return

    thermostats = area.get_thermostats()
    if not thermostats:
        _LOGGER.warning("force_thermostat_update: no thermostats found for area %s", area_id)
        return

    hass = coordinator.hass

    for thermostat_id in thermostats:
        try:
            _LOGGER.info(
                "Diagnostic: Forcing updates for thermostat %s (area=%s)", thermostat_id, area_id
            )

            # Try to find common power switch patterns
            if "." in thermostat_id:
                base = thermostat_id.split(".", 1)[1]
            else:
                base = thermostat_id

            power_switch_patterns = [
                f"switch.{base}_power",
                f"switch.{base}_switch",
                f"switch.{base}",
            ]

            for switch_id in power_switch_patterns:
                state = hass.states.get(switch_id)
                if state:
                    # Turn it on if not on
                    if getattr(state, "state", None) != "on":
                        _LOGGER.info("Diagnostic: Turning on power switch %s", switch_id)
                        await hass.services.async_call(
                            "switch", "turn_on", {"entity_id": switch_id}, blocking=True
                        )

                        # Wait for it to report on (timeout after ~3s)
                        for _ in range(12):
                            await asyncio.sleep(0.25)
                            state = hass.states.get(switch_id)
                            if state and getattr(state, "state", None) == "on":
                                _LOGGER.info("Diagnostic: Switch %s is now on", switch_id)
                                break
                        else:
                            _LOGGER.warning(
                                "Diagnostic: Switch %s did not become 'on' within timeout",
                                switch_id,
                            )
                    break

            # Fallback: ensure climate entity is on
            cstate = hass.states.get(thermostat_id)
            if cstate and getattr(cstate, "state", None) != "on":
                _LOGGER.info("Diagnostic: Calling climate.turn_on for %s", thermostat_id)
                await hass.services.async_call(
                    "climate", "turn_on", {"entity_id": thermostat_id}, blocking=True
                )

            # Set hvac mode if requested
            if hvac_mode:
                _LOGGER.info("Diagnostic: Setting HVAC mode %s for %s", hvac_mode, thermostat_id)
                await hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {"entity_id": thermostat_id, "hvac_mode": hvac_mode},
                    blocking=True,
                )

            # Set temperature if requested
            if target_temp is not None:
                _LOGGER.info(
                    "Diagnostic: Setting temperature %.1f°C for %s", target_temp, thermostat_id
                )
                await hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {"entity_id": thermostat_id, "temperature": target_temp},
                    blocking=True,
                )

            _LOGGER.info("Diagnostic: Completed forcing thermostat %s", thermostat_id)

        except Exception as err:
            _LOGGER.exception(
                "Diagnostic: Error while forcing thermostat %s: %s", thermostat_id, err
            )
