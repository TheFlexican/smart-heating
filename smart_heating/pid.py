"""PID controller implementation for Smart Heating.

- Provides a PID class with manual and automatic gains mode.
- Integrates with heating curve coefficient to scale gains automatically.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

DEADBAND = 0.1


@dataclass
class Error:
    value: float


class PID:
    def __init__(
        self,
        heating_system: str,
        automatic_gain_value: float,
        heating_curve_coefficient: float,
        derivative_time_weight: float = 4.0,
        kp: float = 1.0,
        ki: float = 0.0,
        kd: float = 0.0,
        deadband: float = DEADBAND,
        automatic_gains: bool = False,
        integral_limit: float | None = None,
        output_limit: float = 15.0,
    ) -> None:
        self.heating_system = heating_system
        self.automatic_gain_value = automatic_gain_value
        self._coefficient = heating_curve_coefficient

        self._kp = kp
        self._ki = ki
        self._kd = kd

        self.deadband = deadband
        self.automatic_gains = automatic_gains

        # Anti-windup protection: heating-type-aware defaults
        # Floor heating has high thermal inertia -> larger integral limit
        # Radiators have faster response -> smaller integral limit
        if integral_limit is None:
            self.integral_limit = 50.0 if heating_system == "floor_heating" else 10.0
        else:
            self.integral_limit = integral_limit

        # Output clamping to prevent extreme boiler setpoint adjustments
        self.output_limit = output_limit

        self._last_error = 0.0
        self._integral = 0.0
        self._last_time = time.monotonic()

    def reset(self) -> None:
        self._last_error = 0.0
        self._integral = 0.0
        self._last_time = time.monotonic()

    def _calculate_automatic_gains(
        self, heating_curve_value: float | None
    ) -> tuple[float, float, float]:
        # Oversimplified: scale gains by heating curve intensity
        base_kp = 1.0
        base_ki = 0.02
        base_kd = 0.1

        if heating_curve_value is None:
            return base_kp, base_ki, base_kd

        scale = max(0.1, min(3.0, 1.0 + (heating_curve_value / 40.0)))
        return (
            base_kp * scale * self.automatic_gain_value,
            base_ki * scale * self.automatic_gain_value,
            base_kd * scale * self.automatic_gain_value,
        )

    def update(self, error: Error, heating_curve_value: Optional[float]) -> float:
        now = time.monotonic()
        dt = now - self._last_time
        if dt <= 0:
            dt = 1.0

        # Deadband
        if abs(error.value) <= self.deadband:
            return 0.0

        if self.automatic_gains:
            kp, ki, kd = self._calculate_automatic_gains(heating_curve_value)
        else:
            kp, ki, kd = self._kp, self._ki, self._kd

        # P
        p = kp * error.value

        # I - with anti-windup protection
        self._integral += ki * error.value * dt
        # Clamp integral to prevent windup
        self._integral = max(-self.integral_limit, min(self.integral_limit, self._integral))

        # D
        d = 0.0
        if dt > 0:
            d = kd * (error.value - self._last_error) / dt

        # update state
        self._last_error = error.value
        self._last_time = now

        # Calculate output and clamp to prevent extreme adjustments
        output = p + self._integral + d
        output = max(-self.output_limit, min(self.output_limit, output))
        return output
