"""Pulse Width Modulation (PWM) control for on/off boilers.

A simplified PWM controller that uses a duty-cycle percentage to approximate the
modulated heat output. When a boiler doesn't support relative modulation, it can
be controlled by cycling ON for X seconds and OFF for Y seconds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

from .heating_curve import HeatingCurve
from .setpoint_adjuster import SetpointAdjuster

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CycleConfig:
    min_on_seconds: int = 60
    max_on_seconds: int = 600
    min_off_seconds: int = 60
    max_off_seconds: int = 600


class PWMState:
    def __init__(self, on_time: int, off_time: int, enabled: bool):
        self.on_time = on_time
        self.off_time = off_time
        self.enabled = enabled


class PWM:
    def __init__(
        self,
        cycles: CycleConfig,
        heating_curve: HeatingCurve,
        supports_relative_modulation_management: bool = False,
        automatic_duty_cycle: bool = False,
        force: bool = False,
    ) -> None:
        self._cycles = cycles
        self._heating_curve = heating_curve
        self._supports_relative_modulation_management = supports_relative_modulation_management
        self._automatic_duty_cycle = automatic_duty_cycle
        self._enabled = force or False

        self._last_duty_cycle_percentage: Optional[float] = None
        self._last_on_seconds: int = cycles.min_on_seconds
        self._last_off_seconds: int = cycles.min_off_seconds
        self._last_boiler_temperature: float = 0.0
        self._setpoint_offset = 0.0
        self._setpoint_adjuster = SetpointAdjuster()

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def reset(self) -> None:
        self._last_duty_cycle_percentage = None
        self._last_on_seconds = self._cycles.min_on_seconds
        self._last_off_seconds = self._cycles.min_off_seconds

    def update(self, requested_setpoint: float, boiler_temperature: float) -> None:
        """Update PWM state based on requested setpoint and last known boiler temperature."""
        self._last_boiler_temperature = boiler_temperature
        on, off = self._calculate_duty_cycle(requested_setpoint, boiler_temperature)
        self._last_on_seconds = on
        self._last_off_seconds = off
        self._setpoint_offset = self._setpoint_adjuster.calculate_offset(
            self._last_duty_cycle_percentage or 0.0
        )
        _LOGGER.debug(
            "PWM: on=%s off=%s duty=%.2f",
            on,
            off,
            (self._last_duty_cycle_percentage or 0) * 100,
        )

    def _calculate_duty_cycle(
        self, requested_setpoint: float, boiler_temperature: float
    ) -> Tuple[int, int]:
        base_offset = self._heating_curve.base_offset

        # Ensure boiler_temperature above base offset
        boiler_temperature = max(boiler_temperature, base_offset + 1)

        # Calculate duty cycle percentage
        self._last_duty_cycle_percentage = (requested_setpoint - base_offset) / (
            boiler_temperature - base_offset
        )
        self._last_duty_cycle_percentage = min(max(self._last_duty_cycle_percentage, 0.0), 1.0)

        # Map percentage to seconds within min/max
        on_seconds = int(round(self._last_duty_cycle_percentage * self._cycles.max_on_seconds))
        off_seconds = int(
            round((1 - self._last_duty_cycle_percentage) * self._cycles.max_off_seconds)
        )

        # clamp
        on_seconds = max(self._cycles.min_on_seconds, min(on_seconds, self._cycles.max_on_seconds))
        off_seconds = max(
            self._cycles.min_off_seconds, min(off_seconds, self._cycles.max_off_seconds)
        )

        return on_seconds, off_seconds

    @property
    def duty_cycle(self) -> Optional[Tuple[int, int]]:
        if not self._enabled:
            return None
        return self._last_on_seconds, self._last_off_seconds

    @property
    def last_duty_cycle_percentage(self) -> Optional[float]:
        return self._last_duty_cycle_percentage

    @property
    def setpoint(self) -> float | None:
        if self._last_duty_cycle_percentage is None:
            return None
        base_offset = self._heating_curve.base_offset
        return (
            base_offset
            + ((self._last_duty_cycle_percentage / 4) * (self._heating_curve.value - base_offset))
            if self._heating_curve.value
            else None
        )
