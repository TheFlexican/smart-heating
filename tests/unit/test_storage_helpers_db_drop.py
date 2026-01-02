from unittest.mock import Mock

import pytest
from smart_heating import storage_helpers


class FakeConn:
    def __init__(self):
        self.execs = []

    def execute(self, sql):
        # Record the SQL executed
        try:
            self.execs.append(str(sql))
        except Exception:
            self.execs.append(repr(sql))


class FakeEngine:
    def __init__(self, conn):
        self._conn = conn

    def begin(self):
        class Ctx:
            def __enter__(self_inner):
                return conn

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        conn = self._conn
        return Ctx()


@pytest.mark.asyncio
async def test_drop_tables_invokes_drop_statements(monkeypatch):
    hass = Mock()

    conn = FakeConn()
    engine = FakeEngine(conn)

    recorder = Mock()
    recorder.engine = engine

    # Ensure recorder provides an async_add_executor_job compatible with HA
    async def _rec_run(fn, *a, **k):
        return fn(*a, **k)

    recorder.async_add_executor_job = _rec_run

    # Patch get_recorder_instance used inside storage_helpers
    monkeypatch.setattr(storage_helpers, "get_recorder_instance", lambda hass_arg: recorder)

    # Ensure hass.async_add_executor_job runs the function synchronously in tests
    hass.async_add_executor_job = lambda fn, *args, **kwargs: fn()

    # Run drop function
    await storage_helpers._async_drop_recorder_tables(
        hass,
        [
            "smart_heating_history",
            "smart_heating_events",
        ],
    )

    # Ensure DROP TABLE statements were executed for our tables
    executed_sql = "\n".join(conn.execs)
    assert "DROP TABLE IF EXISTS smart_heating_history" in executed_sql
    assert "DROP TABLE IF EXISTS smart_heating_events" in executed_sql


@pytest.mark.asyncio
async def test_no_recorder_skips_drop(monkeypatch):
    hass = Mock()

    # Patch get_recorder_instance to return None (recorder unavailable)
    monkeypatch.setattr(storage_helpers, "get_recorder_instance", lambda hass_arg: None)

    # Should not raise
    await storage_helpers._async_drop_recorder_tables(hass, ["smart_heating_history"])
