import asyncio
import shutil
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from smart_heating import storage_helpers
from smart_heating.const import DOMAIN


class FakeStore:
    def __init__(self, hass, version, key):
        self.hass = hass
        self.version = version
        self.key = key

    async def async_remove(self):
        if self.key == "bad_key":
            raise RuntimeError("boom")
        # simulate async work
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_async_remove_store_keys_handles_exceptions(monkeypatch):
    removed = []

    async def fake_remove(self):
        if self.key == "bad_key":
            raise RuntimeError("fail")
        removed.append(self.key)

    monkeypatch.setattr(
        storage_helpers,
        "Store",
        lambda hass, v, k: SimpleNamespace(
            async_remove=fake_remove.__get__(SimpleNamespace(key=k), object), key=k
        ),
    )

    hass = Mock()
    # Should not raise even when one key fails
    await storage_helpers._async_remove_store_keys(hass, ["good_key", "bad_key"])


def test_remove_path_removes_and_handles_not_found(tmp_path, monkeypatch):
    # existing directory removed
    d = tmp_path / "storage_dir"
    d.mkdir()
    storage_helpers._remove_path(str(d))
    assert not d.exists()

    # non-existent should not raise
    storage_helpers._remove_path(str(d))

    # simulate other exception
    def _raise(path):
        raise RuntimeError("nope")

    monkeypatch.setattr(shutil, "rmtree", _raise)
    # should not raise
    storage_helpers._remove_path(str(d))


@pytest.mark.asyncio
async def test_clear_all_persistent_data_calls_components(tmp_path, monkeypatch):
    # Prepare fake hass
    hass = SimpleNamespace()
    # config.path('.storage', DOMAIN) should return a real dir
    storage_dir = tmp_path / ".storage" / DOMAIN
    storage_dir.mkdir(parents=True)

    class Cfg:
        def path(self, *parts):
            return str(storage_dir)

    hass.config = Cfg()

    # ensure async_add_executor_job returns an awaitable that runs the function
    async def _run(fn, *a, **k):
        return fn(*a, **k)

    hass.async_add_executor_job = lambda fn, *a, **k: _run(fn, *a, **k)

    removed_keys = []

    class S:
        def __init__(self, hass, v, key):
            self.key = key

        async def async_remove(self):
            removed_keys.append(self.key)

    monkeypatch.setattr(storage_helpers, "Store", S)

    # recorder missing -> skip drops
    monkeypatch.setattr(storage_helpers, "get_recorder_instance", lambda hass_arg: None)

    await storage_helpers.clear_all_persistent_data(hass)

    # store keys should be attempted
    assert "smart_heating_history" in removed_keys or "smart_heating_events" in removed_keys
    # storage dir removed by _remove_path via executor
    assert not storage_dir.exists()


@pytest.mark.asyncio
async def test_async_drop_recorder_tables_handles_execute_error(monkeypatch):
    # recorder with engine whose conn.execute raises should be handled
    class BadConn:
        def execute(self, sql):
            raise RuntimeError("boom")

    class BadEngine:
        def begin(self):
            class Ctx:
                def __enter__(self_inner):
                    return BadConn()

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return Ctx()

    recorder = SimpleNamespace(engine=BadEngine())

    monkeypatch.setattr(storage_helpers, "get_recorder_instance", lambda hass_arg: recorder)

    hass = SimpleNamespace()

    async def _run(fn, *a, **k):
        return fn(*a, **k)

    hass.async_add_executor_job = lambda fn, *a, **k: _run(fn, *a, **k)

    # Should not raise
    await storage_helpers._async_drop_recorder_tables(hass, ["t1"])


@pytest.mark.asyncio
async def test_async_drop_recorder_tables_handles_recorder_exception(monkeypatch):
    # get_recorder_instance raises -> should be caught
    def _bad(hass_arg):
        raise RuntimeError("nope")

    monkeypatch.setattr(storage_helpers, "get_recorder_instance", _bad)

    hass = SimpleNamespace()

    async def _run(fn, *a, **k):
        return fn(*a, **k)

    hass.async_add_executor_job = lambda fn, *a, **k: _run(fn, *a, **k)

    # Should not raise
    await storage_helpers._async_drop_recorder_tables(hass, ["t1"])


def test_async_drop_recorder_tables_skips_invalid_names(monkeypatch):
    calls = []

    class Conn:
        def execute(self, sql):
            calls.append(str(sql))

    class Engine:
        def begin(self):
            class Ctx:
                def __enter__(self_inner):
                    return Conn()

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return Ctx()

    recorder = SimpleNamespace(engine=Engine())
    monkeypatch.setattr(storage_helpers, "get_recorder_instance", lambda hass_arg: recorder)

    hass = SimpleNamespace()

    async def _run(fn, *a, **k):
        return fn(*a, **k)

    hass.async_add_executor_job = lambda fn, *a, **k: _run(fn, *a, **k)

    # include invalid names which should be skipped
    import asyncio

    asyncio.get_event_loop().run_until_complete(
        storage_helpers._async_drop_recorder_tables(
            hass, ["valid_table", "drop;table", "bad name", "__ok"]
        )
    )

    # Only valid_table and __ok cause execute calls
    assert any("valid_table" in s for s in calls)
    assert any("__ok" in s for s in calls)
    assert not any("drop;table" in s for s in calls)
