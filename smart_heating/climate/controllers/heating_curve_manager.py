"""Heating curve controller manager."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from ..temperature_sensors import get_outdoor_temperature_from_weather_entity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ...area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)

# Module-level storage for heating curves per area
_heating_curves: dict[str, Any] = {}  # dict[str, HeatingCurve]


def compute_area_candidate(
    hass: "HomeAssistant",
    area_manager: "AreaManager",
    area_id: str,
    overhead: float,
    advanced_enabled: bool,
    heating_curve_enabled: bool,
) -> Optional[float]:
    """Compute boiler setpoint candidate for a single area.

    Encapsulates heating curve and PID adjustments so the main gateway
    control function stays more readable.
    """
    from ..controllers.pid_controller_manager import apply_pid_adjustment

    area = area_manager.get_area(area_id)
    if not area:
        return None

    # Get outside temperature using centralized helper
    outside_temp = get_outdoor_temperature_from_weather_entity(
        hass, area.boost_manager.weather_entity_id
    )

    # Default candidate: max target + overhead
    candidate = area.target_temperature + overhead

    # Heating curve
    candidate = _apply_heating_curve(
        area_manager, area_id, candidate, outside_temp, advanced_enabled, heating_curve_enabled
    )

    # PID adjustment (area-level setting, no global flag needed)
    candidate = apply_pid_adjustment(area_manager, area_id, candidate)

    return candidate


def _apply_heating_curve(
    area_manager: "AreaManager",
    area_id: str,
    candidate: float,
    outside_temp: Optional[float],
    advanced_enabled: bool,
    heating_curve_enabled: bool,
) -> float:
    """Apply heating curve adjustment to candidate setpoint."""
    from ...heating_curve import HeatingCurve

    if not (advanced_enabled and heating_curve_enabled):
        return candidate

    area = area_manager.get_area(area_id)
    coefficient = area.heating_curve_coefficient or area_manager.default_heating_curve_coefficient
    hc = _heating_curves.get(area_id) or HeatingCurve(
        heating_system=("underfloor" if area.heating_type == "floor_heating" else "radiator"),
        coefficient=coefficient,
    )
    _heating_curves[area_id] = hc
    if outside_temp is not None:
        hc.update(area.target_temperature, outside_temp)
        if hc.value is not None:
            _LOGGER.debug(
                "Heating curve applied for %s: %.1f°C (outdoor: %.1f°C, target: %.1f°C, coefficient: %.2f)",
                area_id,
                hc.value,
                outside_temp,
                area.target_temperature,
                coefficient,
            )
            return hc.value
    return candidate
