"""Tests for DeviceEvent model."""

import re

from smart_heating.models.device_event import DeviceEvent


def test_device_event_now_creates_iso_z_timestamp():
    ev = DeviceEvent.now(
        area_id="a1",
        device_id="d1",
        direction="sent",
        command_type="cmd",
        payload={"v": 1},
    )

    # Timestamp should end with Z and be parseable as ISO8601
    assert ev.timestamp.endswith("Z")
    # Basic ISO8601 check (YYYY-MM-DDTHH:MM:SS)
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ev.timestamp)


def test_device_event_to_from_dict_roundtrip():
    ev = DeviceEvent(
        timestamp="2025-01-01T12:00:00Z",
        area_id="a2",
        device_id="dev1",
        direction="received",
        command_type="status",
        payload={"ok": True},
        status="ok",
        error=None,
    )

    d = ev.to_dict()
    ev2 = DeviceEvent.from_dict(d)

    assert ev2 == ev
