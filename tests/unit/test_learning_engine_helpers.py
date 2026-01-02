"""Tests for LearningEngine helper functions and branches."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.util import dt as dt_util
from smart_heating.features.learning_engine import LearningEngine


@pytest.mark.asyncio
async def test_calculate_outdoor_adjustment():
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    assert await le._async_calculate_outdoor_adjustment(20) == pytest.approx(1.1)
    assert await le._async_calculate_outdoor_adjustment(10) == pytest.approx(1.0)
    assert await le._async_calculate_outdoor_adjustment(2) == pytest.approx(0.9)
    assert await le._async_calculate_outdoor_adjustment(-5) == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_get_outdoor_delegates(monkeypatch):
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    # Patch the helper function to return a known value
    monkeypatch.setattr(
        "smart_heating.features.learning_engine.get_outdoor_temperature_from_weather_entity",
        lambda hass_arg, weather: 12.3,
    )

    val = await le._async_get_outdoor_temperature()
    assert val == pytest.approx(12.3)


@pytest.mark.asyncio
async def test_async_get_recent_heating_rates_filters():
    hass = MagicMock()
    mock_store = MagicMock()
    le = LearningEngine(hass, mock_store)

    # Include some events with heating_rate <= 0 which should be filtered out
    mock_store.async_get_events = AsyncMock(
        return_value=[
            {"heating_rate": 0.2},
            {"heating_rate": -0.1},
            {"heating_rate": 0},
            {"heating_rate": 0.5},
        ]
    )

    rates = await le._async_get_recent_heating_rates("a1", days=30)
    assert rates == [0.2, 0.5]


@pytest.mark.asyncio
async def test_async_predict_heating_time_with_adjustment(monkeypatch):
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    # Prepare enough mock heating rates
    rates = [0.2] * 30
    le._async_get_recent_heating_rates = AsyncMock(return_value=rates)
    le._async_get_outdoor_temperature = AsyncMock(return_value=5.0)
    le._async_calculate_outdoor_adjustment = AsyncMock(return_value=1.0)

    minutes = await le.async_predict_heating_time("a1", 18.0, 21.0)
    assert isinstance(minutes, int)
    # expected minutes = temp_change / (avg_rate * adjustment)
    expected = int((21.0 - 18.0) / (0.2 * 1.0))
    assert minutes == expected


@pytest.mark.asyncio
async def test_predict_heating_time_with_non_positive_change():
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    rates = [0.2] * 30
    le._async_get_recent_heating_rates = AsyncMock(return_value=rates)
    le._async_get_outdoor_temperature = AsyncMock(return_value=None)

    # current_temp >= target_temp should return 0
    minutes = await le.async_predict_heating_time("a1", 22.0, 20.0)
    assert minutes == 0


@pytest.mark.asyncio
async def test_calculate_smart_boost_offset_insufficient():
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    le._async_get_recent_heating_rates = AsyncMock(return_value=[0.1] * 5)
    res = await le.async_calculate_smart_boost_offset("a1")
    assert res is None


@pytest.mark.asyncio
async def test_calculate_smart_boost_offset_returns_value(monkeypatch):
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    # Provide sufficient heating rate samples
    le._async_get_recent_heating_rates = AsyncMock(return_value=[0.2] * 30)
    # Simulate a cold outdoor temperature to increase boost
    le._async_get_outdoor_temperature = AsyncMock(return_value=0.0)

    res = await le.async_calculate_smart_boost_offset("a1")
    assert res is not None
    assert res > 0


@pytest.mark.asyncio
async def test_calculate_smart_boost_offset_negligible():
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    # Provide many very small heating rates so that computed boost is negligible
    le._async_get_recent_heating_rates = AsyncMock(return_value=[0.0001] * 30)
    le._async_get_outdoor_temperature = AsyncMock(return_value=25.0)

    res = await le.async_calculate_smart_boost_offset("a1")
    assert res is None


@pytest.mark.asyncio
async def test_async_get_learning_stats_returns_data():
    hass = MagicMock()
    mock_store = MagicMock()
    le = LearningEngine(hass, mock_store)

    events = [
        {"start_time": "2025-01-01T00:00:00", "heating_rate": 0.2},
        {"start_time": "2025-01-02T00:00:00", "heating_rate": 0.3},
    ]

    mock_store.async_get_events = AsyncMock(side_effect=[events, events])
    mock_store.async_get_event_count = AsyncMock(return_value=2)

    res = await le.async_get_learning_stats("a1")
    assert res["data_points"] == 2
    assert res["total_events_all_time"] == 2
    assert "recent_events" in res
    assert res["recent_events"][0]["timestamp"] == "2025-01-01T00:00:00"


@pytest.mark.asyncio
async def test_async_get_learning_stats_no_events():
    hass = MagicMock()
    mock_store = MagicMock()
    le = LearningEngine(hass, mock_store)

    mock_store.async_get_events = AsyncMock(return_value=[])
    mock_store.async_get_event_count = AsyncMock(return_value=0)

    res = await le.async_get_learning_stats("a1")
    assert res["data_points"] == 0
    assert res["total_events_all_time"] == 0
    assert res["first_event_time"] is None
    assert res["last_event_time"] is None
    assert res["ready_for_predictions"] is False


@pytest.mark.asyncio
async def test_start_end_heating_event_skip_and_record(monkeypatch):
    hass = MagicMock()
    mock_store = MagicMock()
    mock_store.async_record_event = AsyncMock()
    le = LearningEngine(hass, mock_store)

    # Start an event with current temp
    await le.async_start_heating_event("room1", 18.0)
    assert "room1" in le._active_heating_events

    # End immediately -> should be skipped due to short duration
    await le.async_end_heating_event("room1", 18.5)
    mock_store.async_record_event.assert_not_awaited()

    # Start again but make start_time older so duration > 5 min
    await le.async_start_heating_event("room1", 17.0)
    le._active_heating_events["room1"]["start_time"] = dt_util.now() - timedelta(minutes=6)

    await le.async_end_heating_event("room1", 20.0)
    mock_store.async_record_event.assert_awaited()


@pytest.mark.asyncio
async def test_retry_weather_detection_fails(monkeypatch):
    """Ensure retry loop completes and keeps weather entity None when not found."""
    hass = MagicMock()
    hass.states.async_entity_ids.return_value = []
    le = LearningEngine(hass, MagicMock())

    async def _no_sleep(_):
        return

    monkeypatch.setattr("asyncio.sleep", _no_sleep)

    await le._async_retry_weather_detection()
    assert le._weather_entity is None


@pytest.mark.asyncio
async def test_retry_weather_detection_succeeds_after_delay(monkeypatch):
    """Weather entity detected on a retry attempt (not first)."""
    hass = MagicMock()
    le = LearningEngine(hass, MagicMock())

    # Simulate entity present in list
    hass.states.async_entity_ids.return_value = ["weather.home"]

    # First call returns None, second returns a state with temperature
    weather_state = MagicMock()
    weather_state.attributes = {"temperature": 9.5}

    def get_side_effect(entity_id):
        # first time None, afterwards return the weather_state
        if not hasattr(get_side_effect, "calls"):
            get_side_effect.calls = 0
        get_side_effect.calls += 1
        if get_side_effect.calls == 1:
            return None
        return weather_state

    hass.states.get = MagicMock(side_effect=get_side_effect)

    async def _no_sleep(_):
        return

    monkeypatch.setattr("asyncio.sleep", _no_sleep)

    await le._async_retry_weather_detection()
    assert le._weather_entity == "weather.home"
