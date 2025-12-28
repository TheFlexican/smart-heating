"""Temperature tracker for Smart Heating integration."""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

_LOGGER = logging.getLogger(__name__)

# Maximum number of temperature samples to keep per area
MAX_SAMPLES = 100

# Default time window for trend calculation (in minutes)
DEFAULT_TREND_WINDOW = 30


@dataclass
class TemperatureSample:
    """Represents a single temperature measurement."""

    timestamp: datetime
    temperature: float
    target: Optional[float] = None


class TemperatureTracker:
    """Tracks temperature history and calculates trends.

    This component:
    - Maintains a rolling history of temperature measurements per area
    - Calculates temperature trends (rising, falling, stable)
    - Provides insights into heating performance
    - Helps predict when target temperature will be reached
    """

    def __init__(
        self,
        max_samples: int = MAX_SAMPLES,
        trend_window_minutes: int = DEFAULT_TREND_WINDOW,
    ) -> None:
        """Initialize temperature tracker.

        Args:
            max_samples: Maximum number of samples to keep per area
            trend_window_minutes: Time window for trend calculation in minutes
        """
        self._max_samples = max_samples
        self._trend_window = timedelta(minutes=trend_window_minutes)
        self._history: dict[str, deque[TemperatureSample]] = {}

    def record_temperature(
        self,
        area_id: str,
        temperature: float,
        target: Optional[float] = None,
    ) -> None:
        """Record a temperature measurement for an area.

        Args:
            area_id: Area identifier
            temperature: Current temperature in Celsius
            target: Target temperature in Celsius (optional)
        """
        if area_id not in self._history:
            self._history[area_id] = deque(maxlen=self._max_samples)

        sample = TemperatureSample(
            timestamp=datetime.now(),
            temperature=temperature,
            target=target,
        )

        self._history[area_id].append(sample)
        _LOGGER.debug(
            "Recorded temperature for %s: %.1f°C (target: %s°C)",
            area_id,
            temperature,
            target if target is not None else "N/A",
        )

    def get_trend(self, area_id: str) -> Optional[float]:
        """Calculate temperature trend for an area.

        Returns the rate of temperature change in °C/hour over the trend window.

        Args:
            area_id: Area identifier

        Returns:
            Temperature change rate in °C/hour, or None if insufficient data
        """
        if area_id not in self._history or len(self._history[area_id]) < 2:
            return None

        now = datetime.now()
        cutoff = now - self._trend_window

        # Get samples within the trend window
        samples = [s for s in self._history[area_id] if s.timestamp >= cutoff]

        if len(samples) < 2:
            return None

        # Calculate linear trend
        first_sample = samples[0]
        last_sample = samples[-1]

        time_diff = (last_sample.timestamp - first_sample.timestamp).total_seconds() / 3600
        temp_diff = last_sample.temperature - first_sample.temperature

        if time_diff == 0:
            return None

        trend = temp_diff / time_diff
        _LOGGER.debug("Temperature trend for %s: %.2f°C/hour", area_id, trend)
        return trend

    def get_history(self, area_id: str, limit: Optional[int] = None) -> list[TemperatureSample]:
        """Get temperature history for an area.

        Args:
            area_id: Area identifier
            limit: Maximum number of recent samples to return (None for all)

        Returns:
            List of temperature samples, most recent last
        """
        if area_id not in self._history:
            return []

        samples = list(self._history[area_id])
        if limit:
            samples = samples[-limit:]

        return samples

    def clear_history(self, area_id: str) -> None:
        """Clear temperature history for an area.

        Args:
            area_id: Area identifier
        """
        if area_id in self._history:
            self._history[area_id].clear()
            _LOGGER.debug("Cleared temperature history for %s", area_id)

    def clear_all(self) -> None:
        """Clear temperature history for all areas."""
        self._history.clear()
        _LOGGER.debug("Cleared all temperature history")
