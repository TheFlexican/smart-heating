"""Unit tests for OpenTherm API handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from aiohttp import web
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from smart_heating.api.handlers.opentherm import handle_get_opentherm_gateways


class DummyEntry:
    def __init__(
        self,
        entry_id: str,
        title: str,
        data: dict | None = None,
        options: dict | None = None,
    ):
        self.entry_id = entry_id
        self.title = title
        self.data = data or {}
        self.options = options or {}
        # Default to NOT_LOADED so the hass fixture teardown won't attempt unloading
        self.state = ConfigEntryState.NOT_LOADED


@pytest.mark.asyncio
async def test_get_opentherm_gateways(hass: HomeAssistant):
    """Test that the API returns a list of configured gateways."""
    # Create two dummy config entries for opentherm_gw
    entry1 = DummyEntry(entry_id="e1", title="GW1", data={"id": "gateway1"})
    entry2 = DummyEntry(entry_id="e2", title="GW2", options={"id": "gateway2"})
    # Patch hass.config_entries.async_entries to return our dummy entries
    hass.config_entries.async_entries = MagicMock(return_value=[entry1, entry2])

    resp = await handle_get_opentherm_gateways(hass)
    assert isinstance(resp, web.Response)
    import json

    data = json.loads(resp.body.decode())
    assert "gateways" in data
    assert any(g["gateway_id"] == "gateway1" for g in data["gateways"])
    assert any(g["gateway_id"] == "gateway2" for g in data["gateways"])
