from unittest.mock import AsyncMock, MagicMock

from smart_heating.const import DOMAIN
from smart_heating.utils.coordinator_helpers import (
    call_maybe_async,
    get_coordinator,
    get_coordinator_devices,
    safe_coordinator_data,
)


def test_get_coordinator_and_devices_and_safe_data():
    hass = MagicMock()
    coord = MagicMock()
    coord.data = {"areas": {"a1": {"devices": [{"id": "d1"}]}}}
    coord.async_request_refresh = AsyncMock()
    hass.data = {DOMAIN: {"entry1": coord}}

    got = get_coordinator(hass)
    assert got is coord
    devs = get_coordinator_devices(hass, "a1")
    assert "d1" in devs
    data = {"a": 1, "learning_engine": {"heavy": True}}
    safe = safe_coordinator_data(data)
    assert "learning_engine" not in safe


import pytest


@pytest.mark.asyncio
async def test_call_maybe_async_with_sync_and_async():
    # sync function
    def f(x, y):
        return x + y

    res1 = await call_maybe_async(f, 2, 3)
    assert res1 == 5

    # Test the coroutine path using pytest asyncio


@pytest.mark.asyncio
async def test_call_maybe_async_async():
    async def g(x, y):
        return x * y

    val = await call_maybe_async(g, 3, 4)
    assert val == 12
