"""Minimum setpoint controller: dynamic minimum setpoint adjustments.

Monitors return water temperature and optionally adjusts the minimum setpoint to prevent
overshoot during low-load scenarios (ex: many valves closed). The approach is simplified
and uses a configurable adjustment factor.
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


class MinimumSetpoint:
    def __init__(
        self, configured_minimum_setpoint: float = 30.0, adjustment_factor: float = 1.0
    ):
        self._configured_minimum_setpoint = configured_minimum_setpoint
        self._adjustment_factor = adjustment_factor
        self._current_minimum_setpoint = self._configured_minimum_setpoint

    def calculate(self, boiler_state, pwm_state=None) -> None:
        """Calculate the minimum setpoint based on return water temperature and PWM state.

        boiler_state is expected to have `return_temperature` and `flow_temperature` fields.
        pwm_state might contain `duty_cycle` and `enabled`.
        """
        if boiler_state is None:
            return

        return_temp = getattr(boiler_state, "return_temperature", None)
        if return_temp is None:
            return

        # rudimentary: if return temp increases above flow temp - 5, increase min setpoint
        flow_temp = getattr(boiler_state, "flow_temperature", None)
        new_minimum = self._configured_minimum_setpoint

        if flow_temp is not None and return_temp > (flow_temp - 5):
            # calibrate small increase based on difference and adjustment factor
            difference = max(0.0, return_temp - (flow_temp - 5))
            adjustment = difference * (self._adjustment_factor / 5.0)
            new_minimum = self._configured_minimum_setpoint + adjustment

        # ensure not below configured
        if new_minimum < self._configured_minimum_setpoint:
            new_minimum = self._configured_minimum_setpoint

        self._current_minimum_setpoint = round(new_minimum, 1)
        _LOGGER.debug(
            "Calculated new minimum setpoint: %.1f°C.", self._current_minimum_setpoint
        )

    @property
    def current_minimum_setpoint(self) -> float:
        return self._current_minimum_setpoint
