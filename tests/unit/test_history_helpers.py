from types import SimpleNamespace

import pytest
from smart_heating.const import HISTORY_STORAGE_DATABASE
from smart_heating.storage.history import HistoryTracker


@pytest.mark.asyncio
async def test_async_get_database_stats_disabled_by_default(monkeypatch):
    hass = SimpleNamespace()

    # Provide minimal Store replacement to avoid HA internal store access
    class FakeStore:
        def __init__(self, hass, v, key):
            self._data = None

        async def async_load(self):
            return self._data

        async def async_save(self, data):
            self._data = data

    monkeypatch.setattr("smart_heating.storage.history.Store", FakeStore)
    tracker = HistoryTracker(hass)

    res = await tracker.async_get_database_stats()
    assert res["enabled"] is False
    assert "not enabled" in res["message"]


@pytest.mark.asyncio
async def test_async_get_database_stats_enabled(monkeypatch):
    hass = SimpleNamespace()

    class FakeStore:
        def __init__(self, hass, v, key):
            self._data = None

        async def async_load(self):
            return self._data

        async def async_save(self, data):
            self._data = data

    monkeypatch.setattr("smart_heating.storage.history.Store", FakeStore)
    tracker = HistoryTracker(hass)
    # enable DB backend and set dummy table
    tracker._storage_backend = HISTORY_STORAGE_DATABASE
    # Use a real Table object to make SQLAlchemy happy
    from sqlalchemy import Column, Integer, MetaData, Table

    tracker._db_table = Table("smart_heating_history", MetaData(), Column("id", Integer))

    # Fake engine/connection
    class Conn:
        def execute(self, stmt):
            class R:
                def scalar(self):
                    return 42

            return R()

    class Engine:
        def connect(self):
            class Ctx:
                def __enter__(self_inner):
                    return Conn()

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return Ctx()

    recorder = SimpleNamespace(engine=Engine())

    # recorder should expose async_add_executor_job
    async def _run(fn, *a, **k):
        return fn(*a, **k)

    recorder.async_add_executor_job = lambda fn, *a, **k: _run(fn, *a, **k)

    monkeypatch.setattr("smart_heating.storage.history.get_instance", lambda hass_arg: recorder)

    res = await tracker.async_get_database_stats()
    assert res["enabled"] is True
    assert res["total_entries"] == 42


@pytest.mark.asyncio
async def test_async_get_database_stats_handles_no_engine(monkeypatch):
    hass = SimpleNamespace()

    class FakeStore:
        def __init__(self, hass, v, key):
            self._data = None

        async def async_load(self):
            return self._data

        async def async_save(self, data):
            self._data = data

    monkeypatch.setattr("smart_heating.storage.history.Store", FakeStore)
    tracker = HistoryTracker(hass)
    tracker._storage_backend = HISTORY_STORAGE_DATABASE
    # Use a real Table object to make SQLAlchemy happy
    from sqlalchemy import Column, Integer, MetaData, Table

    tracker._db_table = Table("smart_heating_history", MetaData(), Column("id", Integer))

    recorder = SimpleNamespace()
    # no engine present
    monkeypatch.setattr("smart_heating.storage.history.get_instance", lambda hass_arg: recorder)

    res = await tracker.async_get_database_stats()
    assert res["enabled"] is False
    assert "Recorder engine" in res["message"] or "not initialized" in res["message"]
