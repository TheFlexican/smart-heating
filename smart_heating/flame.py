"""Flame status monitoring and health classification.

Tracks flame on/off times, computes median on-duration, cycles/hour and basic duty ratio.
Provides a `Flame` class that can be updated every sample to maintain statistics used by
health checks or short-cycle detection.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class FlameStatus:
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    SHORT_CYCLING = "short_cycling"
    STUCK_ON = "stuck_on"
    STUCK_OFF = "stuck_off"


class Flame:
    def __init__(self):
        self._history = deque(maxlen=200)
        self._on_times = deque(maxlen=60)
        self._off_times = deque(maxlen=60)

        self._last_state = False
        self._last_changed = time.monotonic()

        self._health_status = FlameStatus.UNKNOWN

    def update(self, flame_active: bool) -> None:
        now = time.monotonic()
        if flame_active != self._last_state:
            duration = now - self._last_changed
            if flame_active:
                # Just turned on, log off duration
                self._off_times.append(duration)
            else:
                # Just turned off, log on duration
                self._on_times.append(duration)
            self._last_state = flame_active
            self._last_changed = now

        # recompute health
        self._compute_health()

    def _compute_health(self) -> None:
        # Basic thresholds
        median_on = None
        if self._on_times:
            median_on = sorted(self._on_times)[len(self._on_times) // 2]

        cycles_per_hour = 0.0
        if self._on_times and self._off_times:
            # approximate cycles per hour by counting average cycle duration
            avg_cycle = (sum(self._on_times) / len(self._on_times)) + (
                sum(self._off_times) / len(self._off_times)
            )
            if avg_cycle > 0:
                cycles_per_hour = 3600.0 / avg_cycle

        # Evaluate
        if median_on is not None and median_on < 60 and cycles_per_hour > 6:
            self._health_status = FlameStatus.SHORT_CYCLING
        else:
            self._health_status = FlameStatus.HEALTHY

    @property
    def health_status(self) -> str:
        return self._health_status

    @property
    def median_on_seconds(self) -> Optional[float]:
        if not self._on_times:
            return None
        return sorted(self._on_times)[len(self._on_times) // 2]

    @property
    def cycles_per_hour(self) -> float:
        if not self._on_times or not self._off_times:
            return 0.0
        avg_cycle = (sum(self._on_times) / len(self._on_times)) + (
            sum(self._off_times) / len(self._off_times)
        )
        return 3600.0 / avg_cycle if avg_cycle > 0 else 0.0
