import asyncio
from types import SimpleNamespace

import pytest

from smart_heating.services.area_handlers import (
    async_handle_enable_area,
    async_handle_disable_area,
    async_handle_set_temperature,
)
from smart_heating.const import ATTR_AREA_ID, ATTR_TEMPERATURE


class DummyAreaManager:
    def __init__(self):
        self.saved = False

    def set_area_target_temperature(self, area_id, temp):
        # simple setter for success path
        self.last = (area_id, temp)

    async def async_save(self):
        self.saved = True


class DummyCoordinator:
    def __init__(self, fail: bool = False):
        self.called = False
        self.fail = fail

    async def async_enable_area(self, area_id):
        self.called = True
        if self.fail:
            raise ValueError("enable failed")

    async def async_disable_area(self, area_id):
        self.called = True
        if self.fail:
            raise ValueError("disable failed")

    async def async_request_refresh(self):
        self.called = True


@pytest.mark.asyncio
async def test_async_handle_enable_disable_success():
    call = SimpleNamespace(data={ATTR_AREA_ID: "zone1"})
    coordinator = DummyCoordinator()

    # enable
    await async_handle_enable_area(call, area_manager=None, coordinator=coordinator)
    assert coordinator.called

    coordinator.called = False
    # disable
    await async_handle_disable_area(call, area_manager=None, coordinator=coordinator)
    assert coordinator.called


@pytest.mark.asyncio
async def test_async_handle_enable_disable_error_paths(caplog):
    call = SimpleNamespace(data={ATTR_AREA_ID: "zone1"})
    coordinator = DummyCoordinator(fail=True)

    # Should catch the ValueError and not raise
    await async_handle_enable_area(call, area_manager=None, coordinator=coordinator)
    assert "Failed to enable area" in caplog.text or coordinator.called

    await async_handle_disable_area(call, area_manager=None, coordinator=coordinator)
    assert "Failed to disable area" in caplog.text or coordinator.called


@pytest.mark.asyncio
async def test_async_handle_set_temperature_success_and_error(monkeypatch):
    call = SimpleNamespace(data={ATTR_AREA_ID: "zone1", ATTR_TEMPERATURE: 21.0})
    area_manager = DummyAreaManager()

    class Coord:
        async def async_request_refresh(self):
            self.refreshed = True

    coord = Coord()

    # success path
    await async_handle_set_temperature(call, area_manager, coord)
    assert area_manager.saved

    # error path: setter raises
    class BadAreaManager(DummyAreaManager):
        def set_area_target_temperature(self, area_id, temp):
            raise ValueError("bad")

    bad_mgr = BadAreaManager()
    await async_handle_set_temperature(call, bad_mgr, coord)
