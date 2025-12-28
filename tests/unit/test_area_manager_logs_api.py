"""Tests for AreaManager log retrieval and listener registration helpers."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from smart_heating.core.area_manager import AreaManager
from smart_heating.models.device_event import DeviceEvent


def iso_z(minutes_offset=0):
    return (
        (datetime.now(timezone.utc) - timedelta(minutes=minutes_offset))
        .isoformat()
        .replace("+00:00", "Z")
    )


def make_event(minutes_offset=0, device_id="d1", direction="sent") -> DeviceEvent:
    return DeviceEvent(
        timestamp=iso_z(minutes_offset),
        area_id="a1",
        device_id=device_id,
        direction=direction,
        command_type="cmd",
        payload={"v": 1},
    )


def test_async_get_device_logs_filters():
    hass = MagicMock()
    am = AreaManager(hass)

    # Add events with different times, devices and directions
    ev1 = make_event(10, device_id="d1", direction="sent")
    ev2 = make_event(5, device_id="d2", direction="received")
    ev3 = make_event(0, device_id="d1", direction="sent")

    am.async_add_device_event("a1", ev1)
    am.async_add_device_event("a1", ev2)
    am.async_add_device_event("a1", ev3)

    # No filters -> should return newest-first
    logs = am.async_get_device_logs("a1")
    assert [l["device_id"] for l in logs] == ["d1", "d2", "d1"]

    # Filter by device_id
    logs = am.async_get_device_logs("a1", device_id="d2")
    assert [l["device_id"] for l in logs] == ["d2"]

    # Filter by direction
    logs = am.async_get_device_logs("a1", direction="sent")
    assert all(l["direction"] == "sent" for l in logs)

    # Filter by since (only include events newer or equal than since)
    since = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat().replace("+00:00", "Z")
    logs = am.async_get_device_logs("a1", since=since)
    assert [l["device_id"] for l in logs] == ["d1", "d2"]


def test_since_parsing_invalid_includes_event():
    hass = MagicMock()
    am = AreaManager(hass)

    # Add one event with malformed timestamp
    bad_ev = DeviceEvent(
        timestamp="not-a-date",
        area_id="a1",
        device_id="bad",
        direction="sent",
        command_type="cmd",
        payload={"v": 1},
    )

    am.async_add_device_event("a1", bad_ev)

    since = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")

    logs = am.async_get_device_logs("a1", since=since)
    # If parsing fails, the event should be included
    assert any(l["device_id"] == "bad" for l in logs)


def test_add_remove_device_log_listener():
    hass = MagicMock()
    am = AreaManager(hass)

    def cb(x):
        pass

    am.add_device_log_listener(cb)
    # Adding same listener again should not duplicate
    am.add_device_log_listener(cb)
    assert am._device_service._device_log_listeners.count(cb) == 1

    # Remove listener
    am.remove_device_log_listener(cb)
    assert cb not in am._device_service._device_log_listeners

    # Removing unknown listener should be silent
    am.remove_device_log_listener(cb)
