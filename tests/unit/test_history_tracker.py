from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.const import (
    DEFAULT_HISTORY_RETENTION_DAYS,
    HISTORY_STORAGE_DATABASE,
    HISTORY_STORAGE_JSON,
    MAX_HISTORY_RETENTION_DAYS,
)
from smart_heating.storage.history import HistoryTracker


@pytest.mark.asyncio
async def test_history_json_load_and_cleanup(monkeypatch):
    hass = MagicMock()
    tracker = HistoryTracker(hass, storage_backend=HISTORY_STORAGE_JSON)

    # Prepare store to return history with an old entry
    old_ts = (datetime.now() - timedelta(days=10)).isoformat()
    new_ts = datetime.now().isoformat()
    data = {
        "history": {
            "area1": [
                {
                    "timestamp": old_ts,
                    "current_temperature": 19.0,
                    "target_temperature": 21.0,
                    "state": "idle",
                },
                {
                    "timestamp": new_ts,
                    "current_temperature": 20.0,
                    "target_temperature": 21.0,
                    "state": "heating",
                },
            ]
        },
        "retention_days": 7,
    }

    tracker._store.async_load = AsyncMock(return_value=data)

    await tracker.async_load()

    # old entry should be removed by cleanup
    assert "area1" in tracker._history
    assert len(tracker._history["area1"]) == 1

    # Test get_history for hours filter
    recent = tracker.get_history("area1", hours=1)
    assert isinstance(recent, list)

    # Test set_retention_days invalid
    with pytest.raises(ValueError):
        tracker.set_retention_days(0)


@pytest.mark.asyncio
async def test_history_database_cleanup_and_save(monkeypatch):
    hass = MagicMock()
    tracker = HistoryTracker(hass, storage_backend=HISTORY_STORAGE_DATABASE)

    # Simulate recorder available and _db_table set
    fake_recorder = MagicMock()
    # async_add_executor_job returns number of removed rows
    fake_recorder.async_add_executor_job = AsyncMock(return_value=2)
    monkeypatch.setattr("smart_heating.storage.history.get_instance", lambda hass: fake_recorder)

    tracker._db_table = MagicMock()
    # Patch _async_load_from_database to avoid heavy DB logic
    tracker._async_load_from_database = AsyncMock(return_value=None)

    await tracker._async_cleanup_database()

    fake_recorder.async_add_executor_job.assert_called_once()


@pytest.mark.asyncio
async def test_set_retention_days_valid_and_invalid():
    hass = MagicMock()
    tracker = HistoryTracker(hass)

    # default retention
    assert tracker.get_retention_days() == DEFAULT_HISTORY_RETENTION_DAYS

    # valid change
    tracker.set_retention_days(2)
    assert tracker.get_retention_days() == 2

    # too small
    with pytest.raises(ValueError):
        tracker.set_retention_days(0)

    # too large
    with pytest.raises(ValueError):
        tracker.set_retention_days(MAX_HISTORY_RETENTION_DAYS + 1)


@pytest.mark.asyncio
async def test_record_temperature_limits_and_get_all_history():
    hass = MagicMock()
    tracker = HistoryTracker(hass)

    area = "area_limit_test"

    # Add more than 1000 entries
    for i in range(1005):
        await tracker.async_record_temperature(area, 20.0 + (i * 0.01), 22.0, "heating")

    assert area in tracker._history
    assert len(tracker._history[area]) == 1000

    # first retained entry should correspond to the (1005 - 1000)th original
    first_retained = tracker._history[area][0]["current_temperature"]
    assert pytest.approx(20.0 + 5 * 0.01, rel=1e-3) == first_retained

    # get_all_history should return the internal dict
    all_hist = tracker.get_all_history()
    assert isinstance(all_hist, dict)


def test_get_history_filters_and_state_normalization():
    hass = MagicMock()
    tracker = HistoryTracker(hass)

    area = "area_query"
    now = datetime.now()

    e_old = {
        "timestamp": (now - timedelta(hours=2)).isoformat(),
        "current_temperature": 18.0,
        "target_temperature": 20.0,
        "state": "HEATING",
        "trvs": None,
    }
    e_mid = {
        "timestamp": (now - timedelta(minutes=30)).isoformat(),
        "current_temperature": 19.0,
        "target_temperature": 20.0,
        "state": "IDLE",
        "trvs": None,
    }
    e_now = {
        "timestamp": now.isoformat(),
        "current_temperature": 20.0,
        "target_temperature": 21.0,
        "state": "OFF",
        "trvs": None,
    }

    tracker._history[area] = [e_old, e_mid, e_now]

    # hours filter (last 1 hour) should return mid + now
    res_hours = tracker.get_history(area, hours=1)
    assert len(res_hours) == 2

    # start_time/end_time filter
    start = now - timedelta(hours=3)
    end = now - timedelta(hours=1)
    res_range = tracker.get_history(area, start_time=start, end_time=end)
    # only e_old falls in that closed interval
    assert len(res_range) == 1
    assert res_range[0]["current_temperature"] == 18.0

    # ensure state values normalized to lowercase on return
    out = tracker.get_history(area)
    assert all(entry["state"].islower() for entry in out)


@pytest.mark.asyncio
async def test_async_migrate_storage_invalid_and_same_backend():
    hass = MagicMock()
    tracker = HistoryTracker(hass)

    # same backend
    res_same = await tracker.async_migrate_storage(HISTORY_STORAGE_JSON)
    assert res_same["success"] is False
    assert "Already using" in res_same["message"]

    # invalid backend
    res_invalid = await tracker.async_migrate_storage("invalid_backend")
    assert res_invalid["success"] is False
    assert "Invalid storage backend" in res_invalid["message"]
