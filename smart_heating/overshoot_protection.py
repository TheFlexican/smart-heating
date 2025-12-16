"""Overshoot Protection (OPV) heuristics.

Calculate the Overshoot Protection Value by waiting for boiler to stabilize at 0% modulation
(if supported) and reporting the observed stable boiler flow temperature. The method here is
kept simple: it records a number of samples and determines the average after stabilization.

This routine is intended to be executed as part of a calibration flow (config_flow) and should
pause normal control while running.
"""

from __future__ import annotations

import asyncio
import logging
from statistics import mean
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class OvershootProtection:
    def __init__(self, coordinator, heating_system: str):
        self._coordinator = coordinator
        self._heating_system = heating_system

    async def calculate(self) -> Optional[float]:
        """Try to compute an OPV by waiting for the system to stabilize at theoretical 0% modulation.

        The coordinator must be able to set transformation to 0% (if supported).
        Returns an estimated OPV flow temperature or None if we cannot compute it.
        """
        # If coordinator lacks modulation control, abort
        if not hasattr(self._coordinator, "async_set_control_max_relative_modulation"):
            _LOGGER.debug("Coordinator does not support modulation control; cannot compute OPV")
            return None

        # Try set 0 modulation and wait for a stable flow temperature
        try:
            await self._coordinator.async_set_control_max_relative_modulation(0)
        except Exception as e:
            _LOGGER.warning(f"Failed to set 0% modulation: {e}")
            return None

        # Wait for flame on (if necessary) and collect samples
        samples = []
        for _ in range(20):  # sample for a few cycles, ~20 * 5 sec = ~100s
            await asyncio.sleep(5)
            tmp = getattr(self._coordinator, "boiler_temperature", None)
            if tmp is not None:
                samples.append(tmp)

        if not samples:
            _LOGGER.warning("No samples read while calculating OPV")
            return None

        avg = mean(samples)
        _LOGGER.info(f"Calculated OPV (average at 0%): {avg:.1f}°C from {len(samples)} samples")
        return round(avg, 1)
