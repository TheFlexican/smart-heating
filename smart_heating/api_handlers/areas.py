"""Area API handlers for Smart Heating."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from ..area_manager import AreaManager
from ..const import DOMAIN
from ..models import Area
from ..utils import (
    build_area_response,
    build_device_info,
    get_coordinator,
    get_coordinator_devices,
)

_LOGGER = logging.getLogger(__name__)


def _log_set_temperature_start(area: Area, temperature: float) -> None:
    old_temp = area.target_temperature
    old_effective = area.get_effective_target_temperature()
    preset_context = f", preset={area.preset_mode}" if area.preset_mode != "none" else ""

    _LOGGER.warning(
        "🌡️ API: SET TEMPERATURE for %s: %.1f°C → %.1f°C%s | Effective: %.1f°C → ?",
        area.name,
        old_temp,
        temperature,
        preset_context,
        old_effective,
    )


def _clear_presets_and_overrides(area: Area, temperature: float) -> None:
    # When user manually sets temperature, clear preset mode to use the explicit temperature
    # Otherwise preset temperature will override the user's choice
    if area and area.preset_mode != "none":
        _LOGGER.warning(
            "🔓 Clearing preset %s for %s - using manual temperature %.1f°C",
            area.preset_mode,
            area.name,
            temperature,
        )
        area.preset_mode = "none"

    # Clear manual override mode when user controls temperature via app
    if area and hasattr(area, "manual_override") and area.manual_override:
        _LOGGER.warning("🔓 Clearing manual override for %s - app now in control", area.name)
        area.manual_override = False


def _log_set_temperature_completed(area: Area) -> None:
    new_effective = area.get_effective_target_temperature()
    _LOGGER.warning(
        "✓ Temperature set: %s | Effective: ? → %.1f°C",
        area.name,
        new_effective,
    )


async def _trigger_immediate_updates(area: Area, temperature: float, climate_controller) -> None:
    # Log area device/thermostat state to aid debugging when devices don't respond
    try:
        thermostats = area.get_thermostats()
        _LOGGER.info(
            "Area %s devices=%s thermostats=%s current_temperature=%s hvac_mode=%s enabled=%s",
            area.name,
            list(area.devices.keys()),
            thermostats,
            getattr(area, "current_temperature", None),
            getattr(area, "hvac_mode", None),
            getattr(area, "enabled", None),
        )
    except Exception:
        _LOGGER.debug("Failed to log area device/thermostat state for %s", area.name)

    if not climate_controller:
        return

    await climate_controller.async_control_heating()

    # Proactively update thermostats immediately for user-initiated changes.
    # This helps when area temperature data is missing or when the device
    # needs an immediate command (e.g., airco units that ignore delayed commands).
    # Use the user-set temperature directly, not preset-overridden effective temperature.
    # Skip proactive update if hvac_mode is "off" - don't send commands to disabled devices.
    try:
        thermostats = area.get_thermostats()
        area_hvac = getattr(area, "hvac_mode", "heat")

        # Don't send commands to thermostats when hvac_mode is "off"
        if thermostats and area_hvac != "off":
            current_temp = getattr(area, "current_temperature", None)
            # Use the actual temperature the user just set, not effective (which may be preset-overridden)
            user_target = temperature
            heating_needed = current_temp is None or current_temp < user_target
            # Determine hvac_mode: use "heat" or "cool" based on heating_needed,
            # since some integrations (like LG ThinQ) don't handle "auto" when off
            if area_hvac == "auto" or area_hvac not in ("heat", "cool"):
                hvac_mode = "heat" if heating_needed else "cool"
            else:
                hvac_mode = area_hvac
            _LOGGER.info(
                "Forcing immediate thermostat update for %s (heating=%s target=%.1f hvac_mode=%s)",
                area.name,
                heating_needed,
                user_target,
                hvac_mode,
            )
            # Use device handler on controller when available to perform immediate update
            try:
                await climate_controller.device_handler.async_control_thermostats(
                    area, heating_needed, user_target, hvac_mode=hvac_mode
                )
            except Exception as err:
                _LOGGER.exception(
                    "Failed to proactively update thermostats for %s: %s", area.name, err
                )
    except Exception:
        _LOGGER.debug("Failed to evaluate proactive thermostat update for %s", area.name)

# (rest of file unchanged)
