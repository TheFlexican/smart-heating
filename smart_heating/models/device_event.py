"""Device event model for Smart Heating."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from ..const import TIMEZONE_SUFFIX
from typing import Any, Dict


@dataclass
class DeviceEvent:
    """Represents a single device command/event sent or received.

    Attributes:
        timestamp: ISO8601 timestamp string
        area_id: Area identifier
        device_id: Device identifier
        direction: "sent" or "received"
        command_type: Short string describing the command or event
        payload: Arbitrary payload (dict or string)
        status: Optional status string (e.g., "ok", "error")
        error: Optional error message
    """

    timestamp: str
    area_id: str
    device_id: str
    direction: str
    command_type: str
    payload: Any
    status: str | None = None
    error: str | None = None

    @classmethod
    def now(
        cls,
        area_id: str,
        device_id: str,
        direction: str,
        command_type: str,
        payload: Any,
        status: str | None = None,
        error: str | None = None,
    ) -> "DeviceEvent":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat().replace(TIMEZONE_SUFFIX, "Z"),
            area_id=area_id,
            device_id=device_id,
            direction=direction,
            command_type=command_type,
            payload=payload,
            status=status,
            error=error,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceEvent":
        return cls(**data)
