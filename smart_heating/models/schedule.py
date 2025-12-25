"""Schedule model for Smart Heating integration."""

import logging
from datetime import datetime
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Mapping short day codes to weekday index: 0=Monday .. 6=Sunday
_SHORT_DAY_TO_INDEX = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def _normalize_day_value(day: Any) -> int:
    """Normalize a single day value to an index (0=Monday).

    Accepts integers or short 3-letter codes and raises ValueError on invalid input.
    """
    if isinstance(day, int):
        return int(day % 7)
    if isinstance(day, str):
        key = day.strip().lower()
        if key in _SHORT_DAY_TO_INDEX:
            return _SHORT_DAY_TO_INDEX[key]
        raise ValueError(
            "Invalid 'day' string format: use numeric index (0=Monday) or short code 'mon'"
        )
    raise ValueError("Invalid 'day' type: must be int or short code string")


def _normalize_days_list(days: list[Any] | None) -> list[int] | None:
    """Normalize a list of day entries to indices or return None if input empty/None."""
    if not days:
        return None
    normalized = []
    for item in days:
        if item is None:
            continue
        normalized.append(_normalize_day_value(item))
    return normalized


class Schedule:
    """Representation of a temperature schedule."""

    def __init__(
        self,
        schedule_id: str,
        time: str = "",
        temperature: float | None = None,
        days: list[int] | None = None,
        enabled: bool = True,
        day: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        preset_mode: str | None = None,
        date: str | None = None,
    ) -> None:
        """Initialize a schedule.

        Args:
            schedule_id: Unique identifier
            time: Time in HH:MM format (fallback if start_time not provided)
            temperature: Target temperature (optional if preset_mode is used)
            days: Days of week (mon, tue, etc.) or None for all days
            enabled: Whether schedule is active
            day: Day name (Monday, Tuesday, etc.) - for single day schedules
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            preset_mode: Preset mode name (away, eco, comfort, home, sleep, activity)
            date: Specific date for one-time schedules (YYYY-MM-DD format)
        """
        self.schedule_id = schedule_id
        # Support both old and new formats
        self.time = start_time or time
        self.start_time = start_time or time
        self.end_time = end_time or "23:59"  # Default end time
        self.temperature = temperature
        self.preset_mode = preset_mode
        self.date = date  # Specific date for one-time schedules

        # Use numeric indices internally: 0=Monday .. 6=Sunday

        # If date is specified, this is a date-specific schedule (not recurring weekly)
        if date:
            self.day = None
            self.days = None
        elif day is not None:
            # Normalize provided day value to an index
            normalized_day = _normalize_day_value(day)
            self.day = int(normalized_day)
            self.days = [int(normalized_day)]
        elif days:
            # Normalize provided days list into indices
            self.days = _normalize_days_list(days)
            # Use first day for display (as index)
            self.day = int(self.days[0]) if self.days else 0
        else:
            self.days = [0, 1, 2, 3, 4, 5, 6]
            self.day = 0

        self.enabled = enabled

    def is_active(self, current_time: datetime) -> bool:
        """Check if schedule is active at given time.

        Args:
            current_time: Current datetime

        Returns:
            True if schedule should be active
        """
        if not self.enabled:
            return False

        # Check if this is a date-specific schedule
        if self.date:
            current_date_str = current_time.strftime("%Y-%m-%d")
            if current_date_str != self.date:
                return False
            # Date matches, check time range
            schedule_start = datetime.strptime(self.start_time, "%H:%M").time()
            schedule_end = datetime.strptime(self.end_time, "%H:%M").time()
            current_time_only = current_time.time()
            return schedule_start <= current_time_only < schedule_end

        # Otherwise, check day of week for recurring schedules
        if not self.days:
            return False

        current_day_idx = current_time.weekday()
        if current_day_idx not in self.days:
            return False

        # Check time (within 30 minutes)
        schedule_time = datetime.strptime(self.time, "%H:%M").time()
        current_time_only = current_time.time()

        # Simple time comparison - schedule is active from its time until next schedule
        return current_time_only >= schedule_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.schedule_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "enabled": self.enabled,
        }

        # Add date for date-specific schedules
        if self.date:
            result["date"] = self.date
        # Add days for recurring weekly schedules
        elif self.days:
            # Already stored as indices
            result["days"] = [int(d) for d in self.days]
            # Only include 'day' if it's a single-day schedule
            # If days has multiple values, don't save 'day' to avoid overriding on reload
            if self.day is not None and len(self.days) == 1:
                result["day"] = int(self.day)

        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.preset_mode is not None:
            result["preset_mode"] = self.preset_mode
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        """Create from dictionary."""
        # Convert frontend days format to internal format if needed
        days_data = data.get("days")
        if days_data and isinstance(days_data, list) and days_data:
            # Filter out None before mapping
            days_data = [d for d in days_data if d is not None]

            # Normalize to indices using shared helper
            days_data = [_normalize_day_value(d) for d in days_data]

        # Filter out None values to match type hint list[str] | None
        filtered_days = [int(d) for d in days_data if d is not None] if days_data else None

        # Normalize input 'day' to index if provided as string short code
        day_val = data.get("day")
        if isinstance(day_val, str):
            day_val = _normalize_day_value(day_val)

        return cls(
            schedule_id=data["id"],
            time=data.get("time", ""),
            temperature=data.get("temperature"),
            days=filtered_days,
            enabled=data.get("enabled", True),
            day=day_val,
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            preset_mode=data.get("preset_mode"),
            date=data.get("date"),
        )
