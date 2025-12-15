import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.overshoot_protection import OvershootProtection


@pytest.mark.asyncio
async def test_calculate_no_modulation_support(monkeypatch):
    coord = MagicMock()
    op = OvershootProtection(coord, "radiator")
    res = await op.calculate()
    assert res is None


@pytest.mark.asyncio
async def test_calculate_with_samples(monkeypatch):
    coord = MagicMock()
    coord.async_set_control_max_relative_modulation = AsyncMock()
    coord.boiler_temperature = 50.0
    op = OvershootProtection(coord, "radiator")

    # Patch asyncio.sleep to avoid waiting
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    res = await op.calculate()
    assert abs(res - 50.0) < 1e-6


@pytest.mark.asyncio
async def test_calculate_handles_exception(monkeypatch):
    coord = MagicMock()
    coord.async_set_control_max_relative_modulation = AsyncMock(
        side_effect=Exception("fail")
    )
    op = OvershootProtection(coord, "radiator")

    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    res = await op.calculate()
    assert res is None
