from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import logging
from homeassistant.util import dt as dt_util
from smart_heating.features.learning_engine import MIN_LEARNING_EVENTS, HeatingEvent, LearningEngine


def test_heating_event_metrics():
    start = dt_util.now() - timedelta(minutes=10)
    end = dt_util.now()
    ev = HeatingEvent("a1", start, end, 18.0, 20.0, 5.0)
    assert ev.duration_minutes > 0
    assert abs(ev.heating_rate - (2.0 / ev.duration_minutes)) < 1e-6


@pytest.mark.asyncio
async def test_get_outdoor_temperature_and_predict_heating_time():
    hass = MagicMock()
    mock_event_store = MagicMock()
    le = LearningEngine(hass, mock_event_store)
    le._weather_entity = "weather.home"
    hass.states.get = MagicMock()
    state = MagicMock()
    state.attributes = {"temperature": "12.0"}
    hass.states.get.return_value = state
    t = await le._async_get_outdoor_temperature()
    assert t == pytest.approx(12.0)

    # Test predict heating time with insufficient data
    le._async_get_recent_heating_rates = AsyncMock(return_value=[0.5] * 5)
    res = await le.async_predict_heating_time("a1", 18.0, 21.0)
    assert res is None

    # With enough data
    rates = [0.2] * 30
    le._async_get_recent_heating_rates = AsyncMock(return_value=rates)
    le._async_get_outdoor_temperature = AsyncMock(return_value=10.0)
    le._async_calculate_outdoor_adjustment = AsyncMock(return_value=1.0)
    res2 = await le.async_predict_heating_time("a1", 18.0, 21.0)
    assert isinstance(res2, int)


@pytest.mark.asyncio
async def test_start_end_heating_event_records(monkeypatch):
    hass = MagicMock()
    mock_event_store = MagicMock()
    mock_event_store.async_record_event = AsyncMock()
    le = LearningEngine(hass, mock_event_store)
    le._async_get_outdoor_temperature = AsyncMock(return_value=5.0)
    # Start event
    await le.async_start_heating_event("a1", 18.0)
    assert "a1" in le._active_heating_events

    # Make a start_time in the past to create duration > 5 min
    le._active_heating_events["a1"]["start_time"] = dt_util.now() - timedelta(minutes=6)
    # End event should record to event store
    await le.async_end_heating_event("a1", 21.0)
    mock_event_store.async_record_event.assert_awaited()


"""Tests for learning engine.

Tests the adaptive learning engine including heating event tracking,
statistics recording, and prediction functionality.
"""


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    from smart_heating.const import DOMAIN

    hass.data = {DOMAIN: {}}
    hass.states = MagicMock()
    hass.states.async_entity_ids = MagicMock(return_value=[])
    hass.states.get = MagicMock(return_value=None)
    return hass


@pytest.fixture
def mock_event_store():
    """Create a mock EventStore instance."""
    event_store = MagicMock()
    event_store.async_record_event = AsyncMock()
    event_store.async_get_events = AsyncMock(return_value=[])
    event_store.async_get_event_count = AsyncMock(return_value=0)
    return event_store


@pytest.fixture
def learning_engine(mock_hass, mock_event_store):
    """Create a learning engine instance."""
    return LearningEngine(mock_hass, mock_event_store)


class TestHeatingEvent:
    """Tests for HeatingEvent class."""

    def test_heating_event_creation(self):
        """Test creating a heating event."""
        start_time = dt_util.now()
        end_time = start_time + timedelta(minutes=30)

        event = HeatingEvent(
            area_id="living_room",
            start_time=start_time,
            end_time=end_time,
            start_temp=18.0,
            end_temp=21.0,
            outdoor_temp=10.0,
        )

        assert event.area_id == "living_room"
        assert event.start_time == start_time
        assert event.end_time == end_time
        assert event.start_temp == 18.0
        assert event.end_temp == 21.0
        assert event.outdoor_temp == 10.0
        assert event.duration_minutes == 30.0
        assert event.temp_change == 3.0
        assert event.heating_rate == pytest.approx(0.1, abs=0.01)  # 3°C / 30min

    def test_heating_event_no_outdoor_temp(self):
        """Test creating event without outdoor temperature."""
        start_time = dt_util.now()
        end_time = start_time + timedelta(minutes=20)

        event = HeatingEvent(
            area_id="bedroom",
            start_time=start_time,
            end_time=end_time,
            start_temp=19.0,
            end_temp=21.0,
        )

        assert event.outdoor_temp is None
        assert event.duration_minutes == 20.0
        assert event.temp_change == 2.0

    def test_heating_event_zero_duration(self):
        """Test handling zero duration."""
        now = dt_util.now()

        event = HeatingEvent(
            area_id="test",
            start_time=now,
            end_time=now,
            start_temp=20.0,
            end_temp=20.0,
        )

        assert event.duration_minutes == 0.0
        assert event.heating_rate == 0.0


class TestLearningEngineSetup:
    """Tests for learning engine setup."""

    def test_initialization(self, learning_engine):
        """Test learning engine initialization."""
        assert learning_engine._active_heating_events == {}
        assert learning_engine._weather_entity is None

    @pytest.mark.asyncio
    async def test_async_setup_with_weather_entity(self, learning_engine, mock_hass):
        """Test setup with available weather entity."""
        weather_state = MagicMock()
        weather_state.state = "sunny"

        mock_hass.states.async_entity_ids.return_value = ["weather.home"]
        mock_hass.states.get.return_value = weather_state

        await learning_engine.async_setup()

        assert learning_engine._weather_entity == "weather.home"

    @pytest.mark.asyncio
    async def test_async_setup_no_weather_entity(self, learning_engine, mock_hass):
        """Test setup without weather entity."""
        mock_hass.states.async_entity_ids.return_value = []

        await learning_engine.async_setup()

        assert learning_engine._weather_entity is None

    @pytest.mark.asyncio
    async def test_detect_weather_entity_unavailable(self, learning_engine, mock_hass):
        """Test detection skips unavailable weather entities."""
        weather_state = MagicMock()
        weather_state.state = "unavailable"

        mock_hass.states.async_entity_ids.return_value = ["weather.home"]
        mock_hass.states.get.return_value = weather_state

        entity = await learning_engine._async_detect_weather_entity()
        assert entity is None

    @pytest.mark.asyncio
    async def test_retry_weather_detection_succeeds(self, learning_engine, mock_hass, monkeypatch):
        """Test the retry loop detects a weather entity when available."""
        weather_state = MagicMock()
        weather_state.state = "sunny"
        weather_state.attributes = {"temperature": 11.2}

        mock_hass.states.async_entity_ids.return_value = ["weather.home"]
        mock_hass.states.get.return_value = weather_state

        # Patch asyncio.sleep to avoid delays
        async def _no_sleep(_):
            return

        monkeypatch.setattr("asyncio.sleep", _no_sleep)

        # Run the retry coroutine directly
        await learning_engine._async_retry_weather_detection()
        assert learning_engine._weather_entity == "weather.home"
