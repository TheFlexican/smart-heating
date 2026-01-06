"""Temperature tracker for Smart Heating integration."""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from homeassistant.util import dt as dt_util

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
            timestamp=dt_util.now(),
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

        now = dt_util.now()
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

    def get_latest_temperature(self, area_id: str) -> Optional[float]:
        """Get the most recent temperature for an area.

        Args:
            area_id: Area identifier

        Returns:
            Latest temperature or None if no data
        """
        if area_id not in self._history or not self._history[area_id]:
            return None
        return self._history[area_id][-1].temperature

    def predict_time_to_temperature(
        self,
        area_id: str,
        threshold_temp: float,
    ) -> Optional[float]:
        """Predict minutes until area temperature reaches a threshold.

        Uses current trend to extrapolate when temperature will drop to threshold.
        Only works for falling temperatures (negative trend).

        Args:
            area_id: Area identifier
            threshold_temp: Temperature threshold to reach

        Returns:
            Predicted minutes until threshold is reached, or None if:
            - Trend is positive (rising temperature)
            - Insufficient data for trend calculation
            - Current temperature is already below threshold
        """
        trend = self.get_trend(area_id)
        if trend is None or trend >= 0:
            # No trend data or temperature is rising/stable
            return None

        current_temp = self.get_latest_temperature(area_id)
        if current_temp is None:
            return None

        if current_temp <= threshold_temp:
            # Already at or below threshold
            return 0.0

        # Calculate time to reach threshold
        # trend is in °C/hour (negative), temp_diff is positive
        temp_diff = current_temp - threshold_temp
        hours_to_threshold = temp_diff / abs(trend)
        minutes_to_threshold = hours_to_threshold * 60

        _LOGGER.debug(
            "Predicted time to %.1f°C for %s: %.1f min (current: %.1f°C, trend: %.2f°C/h)",
            threshold_temp,
            area_id,
            minutes_to_threshold,
            current_temp,
            trend,
        )

        return minutes_to_threshold

    def get_trend_confidence(self, area_id: str) -> Optional[float]:
        """Get confidence level of trend calculation.

        Based on number of samples and time span of data.

        Args:
            area_id: Area identifier

        Returns:
            Confidence level 0.0-1.0, or None if insufficient data
        """
        if area_id not in self._history:
            return None

        samples = list(self._history[area_id])
        if len(samples) < 2:
            return None

        now = dt_util.now()
        cutoff = now - self._trend_window

        # Count samples within trend window
        valid_samples = [s for s in samples if s.timestamp >= cutoff]
        sample_count = len(valid_samples)

        if sample_count < 2:
            return None

        # Calculate time span coverage
        if valid_samples:
            time_span = (valid_samples[-1].timestamp - valid_samples[0].timestamp).total_seconds()
            window_seconds = self._trend_window.total_seconds()
            coverage = min(1.0, time_span / window_seconds) if window_seconds > 0 else 0.0
        else:
            coverage = 0.0

        # Confidence based on sample count and coverage
        # More samples and longer time span = higher confidence
        sample_factor = min(1.0, sample_count / 10)  # Max confidence at 10+ samples
        confidence = (sample_factor + coverage) / 2

        return confidence
