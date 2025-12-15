from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.const import HISTORY_STORAGE_DATABASE, HISTORY_STORAGE_JSON
from smart_heating.history import HistoryTracker


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
    monkeypatch.setattr(
        "smart_heating.history.get_instance", lambda hass: fake_recorder
    )

    tracker._db_table = MagicMock()
    # Patch _async_load_from_database to avoid heavy DB logic
    tracker._async_load_from_database = AsyncMock(return_value=None)

    await tracker._async_cleanup_database()

    fake_recorder.async_add_executor_job.assert_called_once()
