"""Tests for AreaManager device event logging and retention."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from smart_heating.core.area_manager import AreaManager
from smart_heating.models.device_event import DeviceEvent


def make_event_with_offset(minutes_offset: int) -> DeviceEvent:
    ts = (
        (datetime.now(timezone.utc) - timedelta(minutes=minutes_offset))
        .isoformat()
        .replace("+00:00", "Z")
    )
    return DeviceEvent(
        timestamp=ts,
        area_id="a1",
        device_id="d1",
        direction="sent",
        command_type="cmd",
        payload={"v": 1},
    )


def test_device_event_retention_purges_old_events():
    hass = MagicMock()
    am = AreaManager(hass)

    # Use small retention window for test
    am._device_service._device_event_retention_minutes = 1

    # Add event that's 120 minutes old -> should be purged
    old_ev = make_event_with_offset(120)
    am.async_add_device_event("a1", old_ev)

    logs = am._device_service._device_logs.get("a1")
    # The old event should have been removed by the purge logic
    assert logs is not None
    assert len(logs) == 0


def test_device_event_recent_is_kept():
    hass = MagicMock()
    am = AreaManager(hass)

    am._device_service._device_event_retention_minutes = 60

    recent_ev = make_event_with_offset(0)
    am.async_add_device_event("a1", recent_ev)

    logs = am._device_service._device_logs.get("a1")
    assert logs is not None
    assert len(logs) == 1
    assert logs[0].timestamp == recent_ev.timestamp
