"""Helpers for adjusting setpoint during PWM ON cycles."""

from __future__ import annotations


class SetpointAdjuster:
    """Small helper: adjust setpoint for duty cycle when boiler is in ON state.

    This keeps a steady effective temperature while the boiler toggles.
    """

    def __init__(self) -> None:
        self._offset = 0.0

    def calculate_offset(self, duty_cycle_percentage: float) -> float:
        """Return a small offset to add when in ON phase to keep the effective setpoint steady.

        This is a simplistic approximation in the first version: linear interpolation.
        """
        # Ensure percentage in [0,1]
        left = max(0.0, min(1.0, duty_cycle_percentage))
        # offset scaling: tuned small values, limited by 3 degrees
        offset = (left - 0.5) * 2 * 1.5
        self._offset = offset
        return offset

    @property
    def offset(self) -> float:
        return self._offset
