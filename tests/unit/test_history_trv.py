"""Tests for history tracker TRV recording."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from smart_heating.storage.history import HistoryTracker


@pytest.mark.asyncio
async def test_async_record_temperature_includes_trvs():
    # Create a fake hass with minimal attributes needed by HistoryTracker
    class FakeHass:
        pass

    hass = FakeHass()
    hass.loop = asyncio.get_event_loop()
    # Minimal hass.data for Store helper
    hass.data = {}
    # Minimal config needed by Store
    hass.config = MagicMock()
    hass.config.config_dir = "/tmp"

    ht = HistoryTracker(hass, storage_backend="json")

    mock_recorder = MagicMock()
    mock_recorder.engine = None  # No DB engine
    with patch("smart_heating.storage.history.get_instance", return_value=mock_recorder):
        await ht.async_load()

    trvs = [
        {"entity_id": "sensor.trv1", "position": 42.0, "open": None, "running_state": "heating"}
    ]

    await ht.async_record_temperature("area_1", 21.0, 22.5, "heating", trvs)

    entries = ht.get_history("area_1")
    assert len(entries) == 1
    entry = entries[0]
    assert "trvs" in entry
    assert isinstance(entry["trvs"], list)
    assert entry["trvs"][0]["entity_id"] == "sensor.trv1"
