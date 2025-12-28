"""Unit tests for EventStore (JSON-path logic and DB fallback)."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.util import dt as dt_util

from smart_heating.const import (
    EVENT_RETENTION_DAYS,
    EVENT_STORAGE_JSON,
    EVENT_STORAGE_DATABASE,
)
from smart_heating.storage.event_store import EventStore


@pytest.mark.asyncio
async def test_load_from_json_and_cleanup(monkeypatch):
    hass = MagicMock()
    store = EventStore(hass, storage_backend=EVENT_STORAGE_JSON)

    # Prepare a mix of old and recent events
    now = dt_util.now()
    old = (now - timedelta(days=EVENT_RETENTION_DAYS + 5)).isoformat()
    recent = now.isoformat()

    data = {
        "events": {
            "area1": [
                {
                    "start_time": old,
                    "end_time": recent,
                    "start_temp": 18.0,
                    "end_temp": 20.0,
                    "duration_minutes": 60.0,
                    "temp_change": 2.0,
                    "heating_rate": 0.033,
                },
                {
                    "start_time": recent,
                    "end_time": recent,
                    "start_temp": 20.0,
                    "end_temp": 21.0,
                    "duration_minutes": 30.0,
                    "temp_change": 1.0,
                    "heating_rate": 0.033,
                },
            ]
        },
        "retention_days": EVENT_RETENTION_DAYS,
    }

    store._store.async_load = AsyncMock(return_value=data)
    store._store.async_save = AsyncMock()

    await store.async_load()

    # Old event should be cleaned up
    assert "area1" in store._events
    assert len(store._events["area1"]) == 1


@pytest.mark.asyncio
async def test_record_and_get_events_and_count():
    hass = MagicMock()
    store = EventStore(hass, storage_backend=EVENT_STORAGE_JSON)

    store._store.async_save = AsyncMock()

    area = "area_rec"
    now = dt_util.now()

    # Create three events spread over days
    ev1 = {
        "start_time": (now - timedelta(days=5)).isoformat(),
        "end_time": (now - timedelta(days=5)).isoformat(),
        "start_temp": 18.0,
        "end_temp": 19.0,
        "duration_minutes": 60.0,
        "temp_change": 1.0,
        "heating_rate": 0.016,
    }
    ev2 = {
        "start_time": (now - timedelta(days=2)).isoformat(),
        "end_time": (now - timedelta(days=2)).isoformat(),
        "start_temp": 19.0,
        "end_temp": 20.0,
        "duration_minutes": 45.0,
        "temp_change": 1.0,
        "heating_rate": 0.022,
    }
    ev3 = {
        "start_time": now.isoformat(),
        "end_time": now.isoformat(),
        "start_temp": 20.0,
        "end_temp": 21.0,
        "duration_minutes": 30.0,
        "temp_change": 1.0,
        "heating_rate": 0.033,
    }

    await store.async_record_event(area, ev1)
    await store.async_record_event(area, ev3)
    await store.async_record_event(area, ev2)

    # Count
    cnt = await store.async_get_event_count(area)
    assert cnt == 3

    # Query last 3 days: should return ev2 and ev3 (ev1 is 5 days ago)
    events_last3 = await store.async_get_events(area, days=3)
    assert len(events_last3) == 2
    # Ensure sorted by start_time ascending
    starts = [e["start_time"] for e in events_last3]
    assert starts[0] <= starts[1]

    # days=None returns all
    all_events = await store.async_get_events(area, days=None)
    assert len(all_events) == 3


@pytest.mark.asyncio
async def test_cleanup_json_removes_older_than_cutoff():
    hass = MagicMock()
    store = EventStore(hass)

    area = "cleanup_area"
    now = dt_util.now()

    old = {
        "start_time": (now - timedelta(days=10)).isoformat(),
        "end_time": now.isoformat(),
        "start_temp": 16.0,
        "end_temp": 18.0,
        "duration_minutes": 100.0,
        "temp_change": 2.0,
        "heating_rate": 0.02,
    }
    recent = {
        "start_time": now.isoformat(),
        "end_time": now.isoformat(),
        "start_temp": 19.0,
        "end_temp": 20.0,
        "duration_minutes": 20.0,
        "temp_change": 1.0,
        "heating_rate": 0.05,
    }

    store._events[area] = [old, recent]
    store._store.async_save = AsyncMock()

    # Set retention days small and run cleanup
    store._retention_days = 1
    await store._async_cleanup_old_events()

    assert area in store._events
    assert len(store._events[area]) == 1
    assert store._events[area][0]["start_temp"] == 19.0


@pytest.mark.asyncio
async def test_close_saves_json_when_json_backend():
    hass = MagicMock()
    store = EventStore(hass)
    store._store.async_save = AsyncMock()

    await store.async_close()

    # When backend is JSON, close should call save
    store._store.async_save.assert_called()


@pytest.mark.asyncio
async def test_record_event_database_fallbacks_to_json_on_db_error(monkeypatch):
    hass = MagicMock()
    store = EventStore(hass, storage_backend=EVENT_STORAGE_DATABASE)

    # Make the recorder throw when used (simulate DB write failure)
    fake_recorder = MagicMock()

    async def failing_executor(job):
        raise RuntimeError("db error")

    fake_recorder.async_add_executor_job = AsyncMock(side_effect=RuntimeError("db error"))
    monkeypatch.setattr(
        "smart_heating.storage.event_store.get_instance", lambda hass: fake_recorder
    )

    # Ensure _store.save to capture fallback
    store._store.async_save = AsyncMock()

    area = "db_fallback"
    ev = {
        "start_time": dt_util.now().isoformat(),
        "end_time": dt_util.now().isoformat(),
        "start_temp": 20.0,
        "end_temp": 21.0,
        "duration_minutes": 10.0,
        "temp_change": 1.0,
        "heating_rate": 0.1,
    }

    # _db_table must be set to try DB path
    store._db_table = MagicMock()

    # Should not raise; fallback to JSON should occur
    await store.async_record_event(area, ev)

    assert area in store._events
    assert len(store._events[area]) == 1
    store._store.async_save.assert_called()


@pytest.mark.asyncio
async def test_deferred_db_validation(monkeypatch):
    """If recorder is unavailable initially we should retry validation later."""
    hass = MagicMock()
    store = EventStore(hass)

    # Simulate get_instance returning None first, then a recorder
    call = {"n": 0}

    def get_instance_stub(h):
        call["n"] += 1
        if call["n"] == 1:
            return None
        fake_rec = MagicMock()
        fake_rec.db_url = "mysql://user:pass@localhost/homeassistant"
        fake_rec.engine = MagicMock()
        fake_rec.async_add_executor_job = AsyncMock()
        return fake_rec

    monkeypatch.setattr("smart_heating.storage.event_store.get_instance", get_instance_stub)

    # First validate (recorder not available) should schedule retry task
    await store._async_validate_database_support()
    assert store._db_validation_task is not None
    assert store._db_validated is False

    # Second validate (recorder available) should complete validation
    await store._async_validate_database_support()
    assert store._db_validated is True
    # DB table should have been initialized
    assert store._db_table is not None
