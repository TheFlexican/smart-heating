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
    """
    from ...minimum_setpoint import MinimumSetpoint

    for aid in heating_area_ids:
        area = area_manager.get_area(aid)
        if not area:
            continue

        minsp = _min_setpoints.get(aid)
        if not minsp:
            default_min = 40.0 if area.heating_type == "floor_heating" else 55.0
            minsp = MinimumSetpoint(configured_minimum_setpoint=default_min, adjustment_factor=1.0)
            _min_setpoints[aid] = minsp

        gateway_state = hass.states.get(gateway_device_id)
        if gateway_state:
            boiler_state = type("_b", (), {})()
            boiler_state.return_temperature = gateway_state.attributes.get(
                "return_water_temp"
            ) or gateway_state.attributes.get("boiler_water_temp")
            boiler_state.flow_temperature = gateway_state.attributes.get("ch_water_temp")
            boiler_state.flame_active = gateway_state.attributes.get("flame_on")
            boiler_state.setpoint = boiler_setpoint
            minsp.calculate(boiler_state)
            if (
                minsp.current_minimum_setpoint is not None
                and boiler_setpoint < minsp.current_minimum_setpoint
            ):
                _LOGGER.debug(
                    "Enforcing minimum setpoint: %.1f°C (was %.1f°C)",
                    minsp.current_minimum_setpoint,
                    boiler_setpoint,
                )
                boiler_setpoint = minsp.current_minimum_setpoint

    return boiler_setpoint
