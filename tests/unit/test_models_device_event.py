"""Tests for DeviceEvent model."""
from datetime import datetime, timezone

from smart_heating.models.device_event import DeviceEvent


def test_device_event_now_iso_z():
    ev = DeviceEvent.now(
        area_id="a1",
        device_id="d1",
        direction="sent",
        command_type="set",
        payload={"value": 1},
    )

    assert isinstance(ev.timestamp, str)
    assert ev.timestamp.endswith("Z")

    # Ensure it parses as timezone-aware ISO 8601 when converting Z -> +00:00
    iso = ev.timestamp.replace("Z", "+00:00")
    dt = datetime.fromisoformat(iso)
    assert dt.tzinfo is not None


def test_device_event_to_from_dict():
    ev = DeviceEvent.now(
        area_id="a1",
        device_id="d1",
        direction="received",
        command_type="state",
        payload={"status": "ok"},
    )
    d = ev.to_dict()
    ev2 = DeviceEvent.from_dict(d)

    assert ev2.area_id == ev.area_id
    assert ev2.device_id == ev.device_id
    assert ev2.direction == ev.direction
    assert ev2.command_type == ev.command_type
    assert ev2.payload == ev.payload
