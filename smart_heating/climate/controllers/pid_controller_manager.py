"""PID controller manager."""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)

# Module-level storage for PID controllers per area
_pids: dict[str, Any] = {}  # dict[str, PID]


def apply_pid_adjustment(
    area_manager: "AreaManager",
    area_id: str,
    candidate: float,
    pid_enabled: bool,
    advanced_enabled: bool,
) -> float:
    """Apply PID adjustment to candidate setpoint."""
    from ...pid import PID, Error

    if not (pid_enabled and advanced_enabled):
        return candidate

    area = area_manager.get_area(area_id)
    if area is None or area.current_temperature is None:
        return candidate

    pid = _pids.get(area_id)
    if not pid:
        pid = PID(
            heating_system=area.heating_type,
            automatic_gain_value=1.0,
            heating_curve_coefficient=(
                area.heating_curve_coefficient or area_manager.default_heating_curve_coefficient
            ),
            automatic_gains=True,
        )
        _pids[area_id] = pid

    err = area.target_temperature - (area.current_temperature or 0.0)

    # Get heating curve value if available
    from ..controllers.heating_curve_manager import _heating_curves

    hc_local = _heating_curves.get(area_id)
    hv = hc_local.value if hc_local and hc_local.value is not None else None
    pid_out = pid.update(Error(err), hv)
    return candidate + pid_out
