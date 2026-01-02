"""Tests for AreaManager listener scheduling of coroutine listeners."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from smart_heating.core.area_manager import AreaManager
from smart_heating.models.device_event import DeviceEvent


def make_recent_event() -> DeviceEvent:
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return DeviceEvent(
        timestamp=ts,
        area_id="a1",
        device_id="d1",
        direction="sent",
        command_type="cmd",
        payload={"v": 1},
    )


@pytest.mark.asyncio
async def test_listener_with_coroutine_scheduled():
    hass = MagicMock()

    # Ensure async_create_task schedules coroutine into running loop
    hass.async_create_task = lambda coro: asyncio.get_running_loop().create_task(coro)

    am = AreaManager(hass)

    ev = make_recent_event()

    event_run = asyncio.Event()

    async def listener(event_dict):
        event_run.set()

    am._device_service._device_log_listeners.append(listener)

    am.async_add_device_event("a1", ev)

    await asyncio.wait_for(event_run.wait(), timeout=1)
    assert event_run.is_set()
