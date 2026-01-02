"""PID controller manager."""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)

# Module-level storage for PID controllers per area
_pids: dict[str, Any] = {}  # dict[str, PID]


def _get_current_area_mode(area: Any) -> str:
    """Detect current operating mode for the area.

    Args:
        area: Area instance

    Returns:
        Current mode string (preset_mode, "schedule", or "manual")
    """
    # Priority: preset_mode if set, otherwise check if schedule is active
    if area.preset_mode and area.preset_mode != "none":
        return area.preset_mode

    # Check if schedule is active by checking if there's an active schedule temperature
    schedule_temp = area.schedule_manager.get_active_schedule_temperature()
    return "schedule" if schedule_temp is not None else "manual"


def _clear_pid_state(area_id: str) -> None:
    """Clear PID controller state for an area to reset integral.

    Args:
        area_id: Area identifier
    """
    if area_id in _pids:
        del _pids[area_id]


def _should_apply_pid(area: Any, current_mode: str) -> bool:
    """Check if PID should be applied for the area in current mode.

    Args:
        area: Area instance
        current_mode: Current operating mode

    Returns:
        True if PID should run, False otherwise
    """
    if not area.pid_enabled:
        return False

    if current_mode not in area.pid_active_modes:
        return False

    return True


def apply_pid_adjustment(
    area_manager: "AreaManager",
    area_id: str,
    candidate: float,
) -> float:
    """Apply PID adjustment to candidate setpoint based on area-level PID settings.

    Args:
        area_manager: AreaManager instance
        area_id: Area identifier
        candidate: Base setpoint candidate from heating curve

    Returns:
        Adjusted setpoint with PID output added, or original candidate if PID not active
    """
    from ...pid import PID, Error

    area = area_manager.get_area(area_id)
    if area is None or area.current_temperature is None:
        return candidate

    # Detect current mode
    current_mode = _get_current_area_mode(area)

    # Check if PID should run
    if not _should_apply_pid(area, current_mode):
        _clear_pid_state(area_id)
        return candidate

    # Get or create PID controller
    pid = _pids.get(area_id)
    if not pid:
        pid = PID(
            heating_system=area.heating_type,
            automatic_gain_value=1.0,
            heating_curve_coefficient=(
                area.heating_curve_coefficient or area_manager.default_heating_curve_coefficient
            ),
            automatic_gains=area.pid_automatic_gains,
        )
        _pids[area_id] = pid

    # Calculate error
    err = area.target_temperature - (area.current_temperature or 0.0)

    # Get heating curve value
    from ..controllers.heating_curve_manager import _heating_curves

    hc_local = _heating_curves.get(area_id)
    hv = hc_local.value if hc_local and hc_local.value is not None else None

    # Update PID and get output
    pid_out = pid.update(Error(err), hv)

    _LOGGER.debug(
        "PID adjustment for %s: mode=%s, output=%.2f°C",
        area_id,
        current_mode,
        pid_out,
    )

    return candidate + pid_out
