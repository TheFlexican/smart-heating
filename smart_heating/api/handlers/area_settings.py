"""Area settings API handlers for Smart Heating."""

import asyncio
import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar

from ...const import DOMAIN
from ...core.area_manager import AreaManager
from ...exceptions import SmartHeatingError
from ...models import Area
from ...utils import get_coordinator
from ..validators import (
    apply_custom_overhead,
    apply_heating_type,
    apply_hysteresis_setting,
    validate_heating_curve_coefficient,
)

_LOGGER = logging.getLogger(__name__)

# Standard error messages
ERROR_INTERNAL = "Internal server error"


def _log_set_temperature_start(area: Area, temperature: float) -> None:
    """Log temperature change start."""
    old_temp = area.target_temperature
    old_effective = area.get_effective_target_temperature()
    preset_context = f", preset={area.preset_mode}" if area.preset_mode != "none" else ""

    _LOGGER.info(
        "API: SET TEMPERATURE for %s: %.1f°C → %.1f°C%s | Effective: %.1f°C → ?",
        area.name,
        old_temp,
        temperature,
        preset_context,
        old_effective,
    )


def _clear_presets_and_overrides(area: Area, temperature: float) -> None:
    """Clear preset mode and enable manual override when user sets temperature."""
    # When user manually sets temperature, clear preset mode to use the explicit temperature
    if area and area.preset_mode != "none":
        _LOGGER.info(
            "Clearing preset %s for %s - using manual temperature %.1f°C",
            area.preset_mode,
            area.name,
            temperature,
        )
        area.preset_mode = "none"

    # Enter manual override mode so automatic sources don't override
    if hasattr(area, "manual_override"):
        if not area.manual_override:
            _LOGGER.info(
                "Setting manual override for %s due to manual temperature set to %.1f°C",
                area.name,
                temperature,
            )
        area.manual_override = True


def _log_set_temperature_completed(area: Area) -> None:
    """Log temperature change completion."""
    new_effective = area.get_effective_target_temperature()
    _LOGGER.info(
        "✓ Temperature set: %s | Effective: ? → %.1f°C",
        area.name,
        new_effective,
    )


async def _trigger_immediate_updates(area: Area, temperature: float, climate_controller) -> None:
    """Trigger immediate updates for climate devices."""
    _log_area_state(area)

    if not climate_controller:
        return

    await climate_controller.async_control_heating()
    await _update_thermostats_immediately(area, temperature, climate_controller)


def _log_area_state(area: Area) -> None:
    """Log area device state for debugging."""
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
    except (AttributeError, KeyError, TypeError) as err:
        _LOGGER.debug(
            "Failed to log area device/thermostat state for %s: %s", area.name, err, exc_info=True
        )


def _determine_hvac_mode(area_hvac: str, heating_needed: bool) -> str:
    """Determine appropriate HVAC mode for thermostat update."""
    if area_hvac == "auto" or area_hvac not in ("heat", "cool"):
        return "heat" if heating_needed else "cool"
    return area_hvac


async def _update_thermostats_immediately(
    area: Area, temperature: float, climate_controller
) -> None:
    """Proactively update thermostats immediately for user-initiated changes."""
    try:
        thermostats = area.get_thermostats()
        area_hvac = getattr(area, "hvac_mode", "heat")

        if not thermostats:
            return
        if area_hvac == "off":
            return

        current_temp = getattr(area, "current_temperature", None)
        heating_needed = current_temp is None or current_temp < temperature
        hvac_mode = _determine_hvac_mode(area_hvac, heating_needed)

        _LOGGER.info(
            "Forcing immediate thermostat update for %s (heating=%s target=%.1f hvac_mode=%s)",
            area.name,
            heating_needed,
            temperature,
            hvac_mode,
        )

        try:
            await climate_controller.device_handler.async_control_thermostats(
                area, heating_needed, temperature, hvac_mode=hvac_mode
            )
        except (HomeAssistantError, SmartHeatingError, asyncio.TimeoutError) as err:
            _LOGGER.error(
                "Failed to proactively update thermostats for %s: %s", area.name, err, exc_info=True
            )
    except (AttributeError, KeyError, TypeError, SmartHeatingError) as err:
        _LOGGER.debug(
            "Failed to evaluate proactive thermostat update for %s: %s",
            area.name,
            err,
            exc_info=True,
        )


async def _refresh_coordinator(hass: HomeAssistant) -> None:
    """Refresh the coordinator if available."""
    coordinator = get_coordinator(hass)
    if coordinator:
        from ...utils.coordinator_helpers import call_maybe_async

        await call_maybe_async(coordinator.async_request_refresh)


async def handle_set_temperature(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set area temperature."""
    from ...utils.validators import validate_area_id, validate_temperature

    # Validate area_id
    is_valid, error_msg = validate_area_id(area_id)
    if not is_valid:
        return web.json_response({"error": error_msg}, status=400)

    # Validate temperature
    temperature = data.get("temperature")
    is_valid, error_msg = validate_temperature(temperature)
    if not is_valid:
        return web.json_response({"error": error_msg}, status=400)
    assert temperature is not None
    temperature = float(temperature)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        _log_set_temperature_start(area, temperature)

        area_manager.set_area_target_temperature(area_id, temperature)
        _clear_presets_and_overrides(area, temperature)

        await area_manager.async_save()

        _log_set_temperature_completed(area)

        # Trigger immediate climate control and proactive updates
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        await _trigger_immediate_updates(area, temperature, climate_controller)

        # Request coordinator refresh
        coordinator = get_coordinator(hass)
        if coordinator:
            from ...utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_enable_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Enable a area."""
    try:
        area_manager.enable_area(area_id)
        await area_manager.async_save()

        # Check if this was the area that triggered a safety alert
        safety_monitor = hass.data.get(DOMAIN, {}).get("safety_monitor")
        if safety_monitor and area_manager.is_safety_alert_active():
            area_manager.set_safety_alert_active(False)
            _LOGGER.info("Safety alert cleared - area '%s' manually re-enabled", area_id)

        # Trigger immediate climate control
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            await climate_controller.async_control_heating()

        await _refresh_coordinator(hass)
        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


async def handle_disable_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Disable a area."""
    try:
        area_manager.disable_area(area_id)
        await area_manager.async_save()

        # Trigger immediate climate control to turn off devices
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            await climate_controller.async_control_heating()

        await _refresh_coordinator(hass)
        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


async def handle_hide_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Hide an area from main view."""
    try:
        area = area_manager.get_area(area_id)
        if not area:
            # Area doesn't exist in storage yet - create it
            area_registry = ar.async_get(hass)
            ha_area = area_registry.async_get_area(area_id)
            if not ha_area:
                return web.json_response(
                    {"error": f"Area {area_id} not found in Home Assistant"}, status=404
                )

            area = Area(
                area_id=area_id,
                name=ha_area.name,
                target_temperature=20.0,
                enabled=True,
            )
            area_manager.add_area(area)

        area.hidden = True
        await area_manager.async_save()
        await _refresh_coordinator(hass)

        return web.json_response({"success": True})
    except (
        HomeAssistantError,
        SmartHeatingError,
        KeyError,
        ValueError,
        AttributeError,
    ) as err:
        _LOGGER.error("API handler error: %s", err, exc_info=True)
        return web.json_response({"error": str(err)}, status=500)


async def handle_unhide_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Unhide an area to show in main view."""
    try:
        area = area_manager.get_area(area_id)
        if not area:
            area_registry = ar.async_get(hass)
            ha_area = area_registry.async_get_area(area_id)
            if not ha_area:
                return web.json_response(
                    {"error": f"Area {area_id} not found in Home Assistant"}, status=404
                )

            area = Area(
                area_id=area_id,
                name=ha_area.name,
                target_temperature=20.0,
                enabled=True,
            )
            area_manager.add_area(area)

        area.hidden = False
        await area_manager.async_save()
        await _refresh_coordinator(hass)

        return web.json_response({"success": True})
    except (
        HomeAssistantError,
        SmartHeatingError,
        KeyError,
        ValueError,
        AttributeError,
    ) as err:
        _LOGGER.error("API handler error: %s", err, exc_info=True)
        return web.json_response({"error": str(err)}, status=500)


async def handle_set_switch_shutdown(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set whether switches/pumps should shutdown when area is not heating."""
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        shutdown = data.get("shutdown", True)
        area.shutdown_switches_when_idle = shutdown
        await area_manager.async_save()

        _LOGGER.info("Area %s: shutdown_switches_when_idle set to %s", area_id, shutdown)
        await _refresh_coordinator(hass)

        return web.json_response({"success": True})
    except (HomeAssistantError, SmartHeatingError, KeyError, ValueError, AttributeError) as err:
        _LOGGER.error("Error setting switch shutdown for area %s", area_id, exc_info=True)
        return web.json_response({"error": ERROR_INTERNAL, "message": str(err)}, status=500)


async def handle_set_area_hysteresis(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set area-specific hysteresis or use global setting."""
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        error_response = apply_hysteresis_setting(area, area_id, data)
        if error_response:
            return error_response

        await area_manager.async_save()
        await _refresh_coordinator(hass)

        return web.json_response({"success": True})
    except (HomeAssistantError, SmartHeatingError, KeyError, ValueError, AttributeError) as err:
        _LOGGER.error("Error setting hysteresis for area %s", area_id, exc_info=True)
        return web.json_response({"error": ERROR_INTERNAL, "message": str(err)}, status=500)


async def handle_set_auto_preset(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set auto preset configuration for area."""
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        # Update auto preset settings (support both 'enabled' and 'auto_preset_enabled')
        if "auto_preset_enabled" in data:
            area.auto_preset_enabled = bool(data["auto_preset_enabled"])
        elif "enabled" in data:
            area.auto_preset_enabled = bool(data["enabled"])

        # Update preset selections
        if "auto_preset_home" in data:
            area.auto_preset_home = str(data["auto_preset_home"])
        elif "home_preset" in data:
            area.auto_preset_home = str(data["home_preset"])

        if "auto_preset_away" in data:
            area.auto_preset_away = str(data["auto_preset_away"])
        elif "away_preset" in data:
            area.auto_preset_away = str(data["away_preset"])

        await area_manager.async_save()
        await _refresh_coordinator(hass)

        return web.json_response({"success": True})
    except (HomeAssistantError, SmartHeatingError, KeyError, ValueError, AttributeError) as err:
        _LOGGER.error("Error setting auto preset for area %s", area_id, exc_info=True)
        return web.json_response({"error": ERROR_INTERNAL, "message": str(err)}, status=500)


async def handle_set_heating_type(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set heating type configuration for area."""
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        # Validate and set heating type
        if "heating_type" in data:
            try:
                apply_heating_type(area, area_id, data["heating_type"])
            except ValueError as err:
                return web.json_response({"error": str(err)}, status=400)

        # Set custom overhead temperature (optional)
        if "custom_overhead_temp" in data:
            try:
                apply_custom_overhead(area, area_id, data["custom_overhead_temp"])
            except ValueError as err:
                return web.json_response({"error": str(err)}, status=400)

        await area_manager.async_save()
        await _refresh_coordinator(hass)

        return web.json_response({"success": True})
    except (HomeAssistantError, SmartHeatingError, KeyError, ValueError, AttributeError) as err:
        _LOGGER.error("Error setting heating type for area %s", area_id, exc_info=True)
        return web.json_response({"error": ERROR_INTERNAL, "message": str(err)}, status=500)


async def handle_set_area_heating_curve(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set per-area heating curve coefficient and whether to use global default."""
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        # Handle use_global flag
        if "use_global" in data:
            use_global = bool(data["use_global"])
            if use_global:
                area.heating_curve_coefficient = None
            elif area.heating_curve_coefficient is None:
                area.heating_curve_coefficient = float(
                    area_manager.default_heating_curve_coefficient
                )

        # Handle coefficient value
        if "coefficient" in data:
            is_valid, result = validate_heating_curve_coefficient(data["coefficient"])
            if not is_valid:
                return web.json_response({"error": result}, status=400)
            area.heating_curve_coefficient = float(result)

        await area_manager.async_save()
        await _refresh_coordinator(hass)

        return web.json_response({"success": True})
    except (HomeAssistantError, SmartHeatingError, KeyError, ValueError, AttributeError) as err:
        _LOGGER.error("Error setting area heating curve for %s", area_id, exc_info=True)
        return web.json_response({"error": ERROR_INTERNAL, "message": str(err)}, status=500)


def _validate_pid_active_modes(active_modes: list) -> tuple[bool, str | list]:
    """Validate PID active modes list.

    Args:
        active_modes: List of mode names

    Returns:
        Tuple of (is_valid, error_message_or_validated_list)
    """
    if not isinstance(active_modes, list):
        return False, "'active_modes' must be a list"

    valid_modes = {"schedule", "home", "away", "sleep", "comfort", "eco", "boost", "manual"}
    for mode in active_modes:
        if mode not in valid_modes:
            return False, f"Invalid mode '{mode}'. Valid modes: {valid_modes}"

    return True, active_modes


async def handle_set_area_pid(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set per-area PID control settings.

    Args:
        hass: Home Assistant instance
        area_manager: AreaManager instance
        area_id: Area identifier
        data: Request data with 'enabled', 'automatic_gains', and 'active_modes'

    Returns:
        JSON response with success status
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        # Handle enabled flag
        if "enabled" in data:
            try:
                area.pid_enabled = bool(data["enabled"])
            except (TypeError, ValueError) as err:
                return web.json_response({"error": f"Invalid 'enabled' value: {err}"}, status=400)

        # Handle automatic_gains flag
        if "automatic_gains" in data:
            try:
                area.pid_automatic_gains = bool(data["automatic_gains"])
            except (TypeError, ValueError) as err:
                return web.json_response(
                    {"error": f"Invalid 'automatic_gains' value: {err}"}, status=400
                )

        # Handle active_modes list
        if "active_modes" in data:
            is_valid, result = _validate_pid_active_modes(data["active_modes"])
            if not is_valid:
                return web.json_response({"error": result}, status=400)
            area.pid_active_modes = result

        await area_manager.async_save()
        await _refresh_coordinator(hass)

        _LOGGER.info(
            "PID settings updated for %s: enabled=%s, automatic_gains=%s, active_modes=%s",
            area.name,
            area.pid_enabled,
            area.pid_automatic_gains,
            area.pid_active_modes,
        )

        return web.json_response({"success": True})
    except Exception as err:
        _LOGGER.error("Error setting area PID for %s", area_id, exc_info=True)
        return web.json_response({"error": ERROR_INTERNAL, "message": str(err)}, status=500)


def _update_area_global_flags(area: Area, data: dict) -> None:
    """Update use_global_* flags on an area."""
    flag_mapping = {
        "use_global_away": "use_global_away",
        "use_global_eco": "use_global_eco",
        "use_global_comfort": "use_global_comfort",
        "use_global_home": "use_global_home",
        "use_global_sleep": "use_global_sleep",
        "use_global_activity": "use_global_activity",
        "use_global_presence": "use_global_presence",
    }

    for key, attr in flag_mapping.items():
        if key in data:
            setattr(area, attr, bool(data[key]))


def _update_area_preset_temps(area: Area, data: dict) -> None:
    """Update preset temperature values on an area."""
    temp_mapping = {
        "away_temp": "away_temp",
        "eco_temp": "eco_temp",
        "comfort_temp": "comfort_temp",
        "home_temp": "home_temp",
        "sleep_temp": "sleep_temp",
        "activity_temp": "activity_temp",
    }

    for key, attr in temp_mapping.items():
        if key in data:
            setattr(area, attr, float(data[key]))


async def handle_set_area_preset_config(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set per-area preset configuration (use global vs custom temperatures)."""
    area = area_manager.get_area(area_id)
    if not area:
        return web.json_response({"error": f"Area {area_id} not found"}, status=404)

    changes = {k: v for k, v in data.items() if k.startswith("use_global_") or k.endswith("_temp")}
    _LOGGER.info("API: SET PRESET CONFIG for %s: %s", area.name, changes)

    # Update use_global_* flags and temperature values
    _update_area_global_flags(area, data)
    _update_area_preset_temps(area, data)

    await area_manager.async_save()

    _LOGGER.info("✓ Preset config saved for %s", area.name)
    await _refresh_coordinator(hass)

    return web.json_response({"success": True})


async def handle_set_manual_override(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Toggle manual override mode for an area."""
    area = area_manager.get_area(area_id)
    if not area:
        return web.json_response({"error": f"Area {area_id} not found"}, status=404)

    enabled = data.get("enabled")
    if enabled is None:
        return web.json_response({"error": "enabled field is required"}, status=400)

    old_state = area.manual_override
    area.manual_override = bool(enabled)

    _LOGGER.info(
        "API: MANUAL OVERRIDE for %s: %s → %s",
        area.name,
        "ON" if old_state else "OFF",
        "ON" if area.manual_override else "OFF",
    )

    # If turning off manual override and there's an active preset, update target to preset temp
    if not area.manual_override and area.preset_mode and area.preset_mode != "none":
        effective_temp = area.get_effective_target_temperature()
        old_target = area.target_temperature
        area.target_temperature = effective_temp
        _LOGGER.warning(
            "✓ %s now using preset mode '%s': %.1f°C → %.1f°C",
            area.name,
            area.preset_mode,
            old_target,
            effective_temp,
        )

    await area_manager.async_save()

    # Trigger climate control to apply changes
    climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
    if climate_controller:
        await climate_controller.async_control_heating()

    await _refresh_coordinator(hass)

    return web.json_response({"success": True})


async def handle_set_primary_temperature_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set the primary temperature sensor for an area."""
    area = area_manager.get_area(area_id)
    if not area:
        return web.json_response({"error": f"Area {area_id} not found"}, status=404)

    sensor_id = data.get("sensor_id")

    # Validate sensor exists in area if not None
    if sensor_id is not None:
        all_temp_devices = area.get_temperature_sensors() + area.get_thermostats()
        if sensor_id not in all_temp_devices:
            return web.json_response(
                {"error": f"Device {sensor_id} not found in area {area_id}"}, status=400
            )

    old_sensor = area.primary_temperature_sensor
    area.primary_temperature_sensor = sensor_id

    _LOGGER.info(
        "API: PRIMARY TEMP SENSOR for %s: %s → %s",
        area.name,
        old_sensor or "Auto (all sensors)",
        sensor_id or "Auto (all sensors)",
    )

    await area_manager.async_save()

    # Update temperatures immediately
    climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
    if climate_controller:
        await climate_controller.async_update_area_temperatures()
        await climate_controller.async_control_heating()

    await _refresh_coordinator(hass)

    return web.json_response({"success": True})
