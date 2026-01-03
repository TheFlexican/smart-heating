"""Minimum setpoint controller manager."""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ...area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)

# Module-level storage for minimum setpoint controllers per area
_min_setpoints: dict[str, Any] = {}  # dict[str, MinimumSetpoint]


def enforce_minimum_setpoints(
    hass: "HomeAssistant",
    area_manager: "AreaManager",
    heating_area_ids: list[str],
    boiler_setpoint: float,
    gateway_device_id: str,
) -> float:
    """Ensure boiler_setpoint respects minimum per-area constraints.

    Returns potentially adjusted boiler_setpoint.

    Uses static minimums based on heating type with optional dynamic adjustments:
    - Radiator: 55°C minimum (can increase dynamically for overshoot protection)
    - Floor heating: 40°C minimum (can increase dynamically for overshoot protection)

    Always enforces the HIGHEST minimum across all active heating areas.
    """
    from ...const import MIN_SETPOINT_FLOOR_HEATING, MIN_SETPOINT_RADIATOR
    from ...minimum_setpoint import MinimumSetpoint

    # Find the highest minimum setpoint required across all active heating areas
    required_minimum = 0.0

    gateway_state = hass.states.get(gateway_device_id)

    for aid in heating_area_ids:
        area = area_manager.get_area(aid)
        if not area:
            continue

        # Start with static minimum based on heating type
        static_minimum = (
            MIN_SETPOINT_RADIATOR if area.heating_type == "radiator" else MIN_SETPOINT_FLOOR_HEATING
        )

        # Apply dynamic adjustment if boiler state available
        area_minimum = static_minimum
        if gateway_state:
            minsp = _min_setpoints.get(aid)
            if not minsp:
                minsp = MinimumSetpoint(
                    configured_minimum_setpoint=static_minimum, adjustment_factor=1.0
                )
                _min_setpoints[aid] = minsp

            # Build boiler state
            boiler_state = type("_b", (), {})()
            boiler_state.return_temperature = gateway_state.attributes.get(
                "return_water_temp"
            ) or gateway_state.attributes.get("boiler_water_temp")
            boiler_state.flow_temperature = gateway_state.attributes.get("ch_water_temp")
            boiler_state.flame_active = gateway_state.attributes.get("flame_on")
            boiler_state.setpoint = boiler_setpoint

            # Calculate dynamic minimum (can only increase, never decrease below static)
            minsp.calculate(boiler_state)
            if minsp.current_minimum_setpoint is not None:
                area_minimum = max(static_minimum, minsp.current_minimum_setpoint)

        # Track highest minimum across all areas
        if area_minimum > required_minimum:
            required_minimum = area_minimum
            _LOGGER.debug(
                "Area %s requires minimum %.1f°C (%s, static: %.1f°C)",
                aid,
                area_minimum,
                area.heating_type,
                static_minimum,
            )

    # Enforce the highest required minimum
    if boiler_setpoint < required_minimum:
        _LOGGER.info(
            "Enforcing minimum setpoint: %.1f°C → %.1f°C (required for active heating types)",
            boiler_setpoint,
            required_minimum,
        )
        return required_minimum

    return boiler_setpoint
