"""Schedule management service."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from ...models import Schedule

_LOGGER = logging.getLogger(__name__)


class ScheduleService:
    """Handles schedule CRUD operations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize schedule service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    def add_schedule_to_area(
        self,
        area: Any,  # Area type to avoid circular import
        schedule_id: str,
        time: str,
        temperature: float,
        days: list[str] | None = None,
    ) -> Schedule:
        """Add a schedule to an area.

        Args:
            area: Area instance
            schedule_id: Unique schedule identifier
            time: Time in HH:MM format
            temperature: Target temperature
            days: Days of week or None for all days

        Returns:
            Created schedule

        Raises:
            ValueError: If schedule validation fails
        """
        schedule = Schedule(schedule_id, time, temperature, days)
        area.add_schedule(schedule)
        _LOGGER.info("Added schedule %s to area %s", schedule_id, area.area_id)
        return schedule

    def remove_schedule_from_area(
        self,
        area: Any,  # Area type to avoid circular import
        schedule_id: str,
    ) -> None:
        """Remove a schedule from an area.

        Args:
            area: Area instance
            schedule_id: Schedule identifier
        """
        area.remove_schedule(schedule_id)
        _LOGGER.info("Removed schedule %s from area %s", schedule_id, area.area_id)

    def get_area_schedules(self, area: Any) -> list[Schedule]:
        """Get all schedules for an area.

        Args:
            area: Area instance

        Returns:
            List of schedules
        """
        return area.schedules

    def update_schedule(
        self,
        area: Any,
        schedule_id: str,
        **updates: Any,
    ) -> Schedule | None:
        """Update a schedule in an area.

        Args:
            area: Area instance
            schedule_id: Schedule identifier
            **updates: Fields to update (time, temperature, days)

        Returns:
            Updated schedule or None if not found
        """
        # Find the schedule
        schedule = None
        for s in area.schedules:
            if s.schedule_id == schedule_id:
                schedule = s
                break

        if not schedule:
            _LOGGER.warning("Schedule %s not found in area %s", schedule_id, area.area_id)
            return None

        # Update fields
        if "time" in updates:
            schedule.time = updates["time"]
        if "temperature" in updates:
            schedule.temperature = updates["temperature"]
        if "days" in updates:
            schedule.days = updates["days"]

        _LOGGER.info("Updated schedule %s in area %s", schedule_id, area.area_id)
        return schedule
