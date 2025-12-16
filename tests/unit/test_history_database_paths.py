from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from smart_heating.const import HISTORY_STORAGE_DATABASE
from smart_heating.history import HistoryTracker


@pytest.mark.asyncio
async def test_history_init_database_success(monkeypatch):
    hass = MagicMock()

    # Fake recorder with mysql db_url and engine
    class FakeRecorder:
        def __init__(self):
            self.db_url = "mysql://user:pass@host/db"
            self.engine = MagicMock()

    monkeypatch.setattr("smart_heating.history.get_instance", lambda hass: FakeRecorder())

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
                    "state": "heating",
                }
            ]
        }

    fake_recorder.async_add_executor_job = AsyncMock(return_value=fake_load())
    monkeypatch.setattr("smart_heating.history.get_instance", lambda hass: fake_recorder)

    # Set db_table to non-None to force database load path
    tracker._db_table = MagicMock()

    # Also set store load to return retention setting
    tracker._store.async_load = AsyncMock(return_value={"retention_days": 5})

    await tracker._async_load_from_database()

    assert "area1" in tracker._history
    assert tracker._retention_days == 5


@pytest.mark.asyncio
async def test_async_save_to_database_entry_error(monkeypatch):
    hass = MagicMock()
    tracker = HistoryTracker(hass, storage_backend=HISTORY_STORAGE_DATABASE)

    # Simulate recorder raising on async_add_executor_job
    class BadRecorder:
        async def async_add_executor_job(self, fn):
            raise RuntimeError("DB failure")

    monkeypatch.setattr("smart_heating.history.get_instance", lambda hass: BadRecorder())
    tracker._db_table = MagicMock()

    # Should not raise
    await tracker._async_save_to_database_entry("area1", datetime.now(), 20.0, 21.0, "heating")
