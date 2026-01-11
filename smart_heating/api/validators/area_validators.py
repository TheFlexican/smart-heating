"""Area-specific validation functions for API handlers."""

import logging

from aiohttp import web

from ...models import Area

_LOGGER = logging.getLogger(__name__)


def apply_heating_type(area: Area, area_id: str, heating_type: str) -> None:
    """Validate and apply heating type to an area.

    Args:
        area: Area instance to modify
        area_id: Area identifier for logging
        heating_type: Heating type to apply

    Raises:
        ValueError: If heating_type is invalid
    """
    if heating_type not in ["radiator", "floor_heating", "airco"]:
        raise ValueError("heating_type must be 'radiator', 'floor_heating' or 'airco'")

    area.heating_type = heating_type
    _LOGGER.info("Area %s: Setting heating_type to %s", area_id, heating_type)

    # If area is switched to air conditioning, clear/disable
    # settings that apply only to radiator/floor heating systems
    if heating_type == "airco":
        area.custom_overhead_temp = None
        area.heating_curve_coefficient = None
        area.hysteresis_override = None
        # Avoid shutting down switches by default for airco
        area.shutdown_switches_when_idle = False


def apply_custom_overhead(area: Area, area_id: str, custom_overhead: float | None) -> None:
    """Validate and apply custom overhead temperature (or clear it).

    Args:
        area: Area instance to modify
        area_id: Area identifier for logging
        custom_overhead: Overhead temperature value or None to clear

    Raises:
        ValueError: If custom_overhead is out of valid range
    """
    if custom_overhead is not None:
        # Validate range
        if custom_overhead < 0 or custom_overhead > 30:
            raise ValueError("custom_overhead_temp must be between 0 and 30°C")
        area.custom_overhead_temp = float(custom_overhead)
        _LOGGER.info("Area %s: Setting custom_overhead_temp to %.1f°C", area_id, custom_overhead)
    else:
        area.custom_overhead_temp = None
        _LOGGER.info("Area %s: Clearing custom_overhead_temp", area_id)


def validate_heating_curve_coefficient(coeff_str: str) -> tuple[bool, str | float]:
    """Validate heating curve coefficient value.

    Args:
        coeff_str: Coefficient value as string

    Returns:
        Tuple of (is_valid, error_message_or_value)
    """
    try:
        coeff = float(coeff_str)
    except (TypeError, ValueError):
        return False, "Invalid coefficient"

    if coeff <= 0 or coeff > 10:
        return False, "Coefficient must be > 0 and <= 10"

    return True, coeff


def apply_hysteresis_setting(area: Area, area_id: str, data: dict) -> web.Response | None:
    """Apply hysteresis setting to area.

    Args:
        area: Area instance
        area_id: Area identifier
        data: Request data

    Returns:
        Error response if validation fails, None if successful
    """
    use_global = data.get("use_global", False)

    if use_global:
        area.hysteresis_override = None
        _LOGGER.info("Area %s: Setting hysteresis_override to None (global)", area_id)
        return None

    # Area-specific hysteresis
    hysteresis = data.get("hysteresis")
    if hysteresis is None:
        return web.json_response(
            {"error": "hysteresis value required when use_global is false"},
            status=400,
        )

    # Validate range (allow 0.0 for exact temperature control)
    if hysteresis < 0.0 or hysteresis > 2.0:
        return web.json_response({"error": "Hysteresis must be between 0.0 and 2.0°C"}, status=400)

    area.hysteresis_override = float(hysteresis)
    _LOGGER.info("Area %s: Setting hysteresis_override to %.1f°C", area_id, hysteresis)
    return None
