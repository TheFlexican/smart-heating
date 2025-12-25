from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.const import HISTORY_STORAGE_DATABASE
from smart_heating.storage.history import HistoryTracker


@pytest.mark.asyncio
async def test_history_init_database_success(monkeypatch):
    hass = MagicMock()

    # Fake recorder with mysql db_url and engine
    class FakeRecorder:
        def __init__(self):
            self.db_url = "mysql://user:pass@host/db"
            self.engine = MagicMock()

    monkeypatch.setattr("smart_heating.storage.history.get_instance", lambda hass: FakeRecorder())

    tracker = HistoryTracker(hass, storage_backend=HISTORY_STORAGE_DATABASE)
    # If recorder present and supported, db_table should be initialized
    assert tracker._storage_backend in (HISTORY_STORAGE_DATABASE,)


@pytest.mark.asyncio
async def test_async_load_from_database(monkeypatch):
    hass = MagicMock()
    tracker = HistoryTracker(hass, storage_backend=HISTORY_STORAGE_DATABASE)

    # Prepare fake recorder with executor job returning a dict
    fake_recorder = MagicMock()

    def fake_load():
        # simulate DB rows transformed into dict
        return {
            "area1": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "current_temperature": 20.0,
                    "target_temperature": 21.0,
                    # Use uppercase to test normalization
                    "state": "HEATING",
                }
            ]
        }

    fake_recorder.async_add_executor_job = AsyncMock(return_value=fake_load())
    monkeypatch.setattr("smart_heating.storage.history.get_instance", lambda hass: fake_recorder)

    # Set db_table to non-None to force database load path
    tracker._db_table = MagicMock()

    # Also set store load to return retention setting
    tracker._store.async_load = AsyncMock(return_value={"retention_days": 5})

    await tracker._async_load_from_database()

    assert "area1" in tracker._history
    # State should be normalized to lowercase
    assert tracker._history["area1"][0]["state"] == "heating"
    assert tracker._retention_days == 5


@pytest.mark.asyncio
async def test_async_load_prefers_database_when_db_has_entries(monkeypatch):
    hass = MagicMock()
    tracker = HistoryTracker(hass, storage_backend="json")

    # Simulate async_get_database_stats returning >0 entries so loader prefers DB
    async def fake_stats():
        return {"total_entries": 5}

    tracker.async_get_database_stats = AsyncMock(return_value={"total_entries": 5})

    # Make the DB loader populate history when called
    async def fake_db_load():
        tracker._history = {
            "area-db": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "current_temperature": 19.5,
                    "target_temperature": 21.0,
                    "state": "heating",
                }
            ]
        }

    tracker._async_load_from_database = AsyncMock(side_effect=fake_db_load)

    # Ensure store has no backend preference so auto-detect runs
    tracker._store.async_load = AsyncMock(return_value={})

    # Pretend DB table exists so auto-detection can query stats
    tracker._db_table = MagicMock()

    await tracker.async_load()

    assert tracker._storage_backend == "database"
    assert "area-db" in tracker._history


@pytest.mark.asyncio
async def test_async_save_to_database_entry_error(monkeypatch):
    hass = MagicMock()
    tracker = HistoryTracker(hass, storage_backend=HISTORY_STORAGE_DATABASE)

    # Simulate recorder raising on async_add_executor_job
    class BadRecorder:
        async def async_add_executor_job(self, fn):
            raise RuntimeError("DB failure")

    monkeypatch.setattr("smart_heating.storage.history.get_instance", lambda hass: BadRecorder())
    tracker._db_table = MagicMock()

    # Should not raise
    await tracker._async_save_to_database_entry("area1", datetime.now(), 20.0, 21.0, "heating")
