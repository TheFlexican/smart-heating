"""Tests for TemperatureTracker."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from smart_heating.core.coordination.temperature_tracker import (
    TemperatureTracker,
    TemperatureSample,
    MAX_SAMPLES,
    DEFAULT_TREND_WINDOW,
)


class TestTemperatureSample:
    """Test TemperatureSample dataclass."""

    def test_temperature_sample_creation(self):
        """Test creating a temperature sample."""
        now = datetime.now()
        sample = TemperatureSample(timestamp=now, temperature=20.5, target=21.0)

        assert sample.timestamp == now
        assert sample.temperature == 20.5
        assert sample.target == 21.0

    def test_temperature_sample_without_target(self):
        """Test creating a temperature sample without target."""
        now = datetime.now()
        sample = TemperatureSample(timestamp=now, temperature=20.5)

        assert sample.timestamp == now
        assert sample.temperature == 20.5
        assert sample.target is None


class TestTemperatureTracker:
    """Test TemperatureTracker functionality."""

    def test_init_default(self):
        """Test initialization with default values."""
        tracker = TemperatureTracker()
        assert tracker._max_samples == MAX_SAMPLES
        assert tracker._trend_window == timedelta(minutes=DEFAULT_TREND_WINDOW)
        assert len(tracker._history) == 0

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        tracker = TemperatureTracker(max_samples=50, trend_window_minutes=15)
        assert tracker._max_samples == 50
        assert tracker._trend_window == timedelta(minutes=15)

    def test_record_temperature(self):
        """Test recording a temperature measurement."""
        tracker = TemperatureTracker()
        tracker.record_temperature("living_room", 20.5, 21.0)

        history = tracker.get_history("living_room")
        assert len(history) == 1
        assert history[0].temperature == 20.5
        assert history[0].target == 21.0

    def test_record_temperature_without_target(self):
        """Test recording temperature without target."""
        tracker = TemperatureTracker()
        tracker.record_temperature("living_room", 20.5)

        history = tracker.get_history("living_room")
        assert len(history) == 1
        assert history[0].temperature == 20.5
        assert history[0].target is None

    def test_record_multiple_temperatures(self):
        """Test recording multiple temperature measurements."""
        tracker = TemperatureTracker()
        tracker.record_temperature("living_room", 20.0)
        tracker.record_temperature("living_room", 20.5)
        tracker.record_temperature("living_room", 21.0)

        history = tracker.get_history("living_room")
        assert len(history) == 3
        assert history[0].temperature == 20.0
        assert history[1].temperature == 20.5
        assert history[2].temperature == 21.0

    def test_record_temperature_multiple_areas(self):
        """Test recording temperatures for multiple areas."""
        tracker = TemperatureTracker()
        tracker.record_temperature("living_room", 20.0)
        tracker.record_temperature("bedroom", 19.0)

        living_room_history = tracker.get_history("living_room")
        bedroom_history = tracker.get_history("bedroom")

        assert len(living_room_history) == 1
        assert len(bedroom_history) == 1
        assert living_room_history[0].temperature == 20.0
        assert bedroom_history[0].temperature == 19.0

    def test_max_samples_limit(self):
        """Test that history is limited to max_samples."""
        tracker = TemperatureTracker(max_samples=5)

        # Record 10 samples
        for i in range(10):
            tracker.record_temperature("living_room", 20.0 + i)

        history = tracker.get_history("living_room")
        assert len(history) == 5  # Should only keep last 5

        # Should have samples 5-9
        assert history[0].temperature == 25.0
        assert history[4].temperature == 29.0

    def test_get_history_empty(self):
        """Test getting history for area with no samples."""
        tracker = TemperatureTracker()
        history = tracker.get_history("living_room")
        assert len(history) == 0

    def test_get_history_with_limit(self):
        """Test getting limited history."""
        tracker = TemperatureTracker()

        # Record 10 samples
        for i in range(10):
            tracker.record_temperature("living_room", 20.0 + i)

        history = tracker.get_history("living_room", limit=3)
        assert len(history) == 3

        # Should be the last 3 samples
        assert history[0].temperature == 27.0
        assert history[1].temperature == 28.0
        assert history[2].temperature == 29.0

    def test_get_trend_insufficient_data(self):
        """Test trend calculation with insufficient data."""
        tracker = TemperatureTracker()
        trend = tracker.get_trend("living_room")
        assert trend is None

        # Single sample is not enough
        tracker.record_temperature("living_room", 20.0)
        trend = tracker.get_trend("living_room")
        assert trend is None

    @patch("smart_heating.core.coordination.temperature_tracker.datetime")
    def test_get_trend_rising(self, mock_datetime):
        """Test trend calculation with rising temperature."""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = base_time + timedelta(minutes=20)

        tracker = TemperatureTracker(trend_window_minutes=30)

        # Manually create samples with specific timestamps
        tracker._history["living_room"] = tracker._history.get(
            "living_room", __import__("collections").deque(maxlen=tracker._max_samples)
        )

        # Add samples showing temperature rise over 20 minutes
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time, temperature=20.0)
        )
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time + timedelta(minutes=10), temperature=20.5)
        )
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time + timedelta(minutes=20), temperature=21.0)
        )

        trend = tracker.get_trend("living_room")
        assert trend is not None
        assert trend > 0  # Temperature is rising
        # 1°C over 20 minutes = 3°C/hour
        assert pytest.approx(trend, abs=0.1) == 3.0

    @patch("smart_heating.core.coordination.temperature_tracker.datetime")
    def test_get_trend_falling(self, mock_datetime):
        """Test trend calculation with falling temperature."""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = base_time + timedelta(minutes=30)

        tracker = TemperatureTracker(trend_window_minutes=30)

        # Manually create samples with specific timestamps
        tracker._history["living_room"] = __import__("collections").deque(
            maxlen=tracker._max_samples
        )

        # Add samples showing temperature fall over 30 minutes
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time, temperature=22.0)
        )
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time + timedelta(minutes=15), temperature=21.0)
        )
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time + timedelta(minutes=30), temperature=20.0)
        )

        trend = tracker.get_trend("living_room")
        assert trend is not None
        assert trend < 0  # Temperature is falling
        # -2°C over 30 minutes = -4°C/hour
        assert pytest.approx(trend, abs=0.1) == -4.0

    @patch("smart_heating.core.coordination.temperature_tracker.datetime")
    def test_get_trend_outside_window(self, mock_datetime):
        """Test that trend only considers samples within the time window."""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = base_time + timedelta(minutes=60)

        tracker = TemperatureTracker(trend_window_minutes=30)

        # Manually create samples with specific timestamps
        tracker._history["living_room"] = __import__("collections").deque(
            maxlen=tracker._max_samples
        )

        # Old sample outside window (60 minutes ago)
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time, temperature=15.0)
        )

        # Recent samples within window
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time + timedelta(minutes=40), temperature=20.0)
        )
        tracker._history["living_room"].append(
            TemperatureSample(timestamp=base_time + timedelta(minutes=60), temperature=21.0)
        )

        trend = tracker.get_trend("living_room")
        assert trend is not None
        # Should only consider samples from minute 40 to 60
        # 1°C over 20 minutes = 3°C/hour
        assert pytest.approx(trend, abs=0.1) == 3.0

    def test_clear_history(self):
        """Test clearing history for an area."""
        tracker = TemperatureTracker()
        tracker.record_temperature("living_room", 20.0)
        tracker.record_temperature("living_room", 21.0)

        assert len(tracker.get_history("living_room")) == 2

        tracker.clear_history("living_room")
        assert len(tracker.get_history("living_room")) == 0

    def test_clear_history_nonexistent_area(self):
        """Test clearing history for non-existent area."""
        tracker = TemperatureTracker()
        tracker.clear_history("living_room")  # Should not raise

    def test_clear_all(self):
        """Test clearing all history."""
        tracker = TemperatureTracker()
        tracker.record_temperature("living_room", 20.0)
        tracker.record_temperature("bedroom", 19.0)

        assert len(tracker.get_history("living_room")) == 1
        assert len(tracker.get_history("bedroom")) == 1

        tracker.clear_all()
        assert len(tracker.get_history("living_room")) == 0
        assert len(tracker.get_history("bedroom")) == 0
        assert len(tracker._history) == 0
