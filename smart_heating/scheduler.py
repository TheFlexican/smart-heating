"""Schedule executor for Zone Heater Manager."""

import logging
from datetime import datetime, time, timedelta
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .area_manager import AreaManager
from .models import Area, Schedule

_LOGGER = logging.getLogger(__name__)

SCHEDULE_CHECK_INTERVAL = timedelta(minutes=1)  # Check schedules every minute

DAYS_OF_WEEK = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


class ScheduleExecutor:
    """Execute area schedules to control temperatures."""

    def __init__(
        self, hass: HomeAssistant, area_manager: AreaManager, learning_engine=None
    ) -> None:
        """Initialize the schedule executor.

        Args:
            hass: Home Assistant instance
            area_manager: Zone manager instance
            learning_engine: Optional learning engine for predictive scheduling
        """
        self.hass = hass
        self.area_manager = area_manager
        self.learning_engine = learning_engine
        self._unsub_interval = None
        self._last_applied_schedule = {}  # Track last applied schedule per area
        _LOGGER.info("Schedule executor initialized")

    async def async_start(self) -> None:
        """Start the schedule executor."""
        _LOGGER.info("Starting schedule executor")

        # Run immediately on start
        await self._async_check_schedules()

        # Set up recurring check
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_check_schedules,
            SCHEDULE_CHECK_INTERVAL,
        )
        _LOGGER.info("Schedule executor started, checking every %s", SCHEDULE_CHECK_INTERVAL)

    def async_stop(self) -> None:
        """Stop the schedule executor."""
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None
        _LOGGER.info("Schedule executor stopped")

    def clear_schedule_cache(self, area_id: str) -> None:
        """Clear the last applied schedule cache for an area.

        This should be called when a schedule is removed or modified
        to ensure the scheduler re-evaluates and applies the current schedule.

        Args:
            area_id: Area identifier
        """
        if area_id in self._last_applied_schedule:
            del self._last_applied_schedule[area_id]
            _LOGGER.debug("Cleared schedule cache for area %s", area_id)

    async def _async_check_schedules(self, now: Optional[datetime] = None) -> None:
        """Check all area schedules and apply temperatures if needed.

        Also handles smart night boost by predicting heating start times.

        Args:
            now: Current datetime (for testing, otherwise uses current time)
        """
        # Get current UTC time and convert to HA's configured timezone
        if now is None:
            now = dt_util.utcnow()

        # Always convert to HA's configured timezone
        if self.hass.config.time_zone:
            import zoneinfo

            tz = zoneinfo.ZoneInfo(self.hass.config.time_zone)
            now = now.astimezone(tz)

        current_time = now.time()
        current_day_idx = now.weekday()

        _LOGGER.debug(
            "Checking schedules for %s at %s",
            DAYS_OF_WEEK[current_day_idx],
            current_time.strftime("%H:%M"),
        )

        areas = self.area_manager.get_all_areas()

        for area_id, area in areas.items():
            await self._process_area_schedules(area_id, area, now, current_day_idx, current_time)

    async def _process_area_schedules(
        self, area_id: str, area: Area, now: datetime, current_day_idx: int, current_time: time
    ) -> None:
        """Process schedules for a single area.

        Extracted from _async_check_schedules to reduce cognitive complexity.
        """
        if not area.enabled:
            _LOGGER.debug("Area %s is disabled, skipping schedule check", area.name)
            return

        # Handle smart night boost prediction
        if area.smart_night_boost_enabled and self.learning_engine:
            await self._handle_smart_night_boost(area, now)

        if not area.schedules:
            return

        # Find active schedule for current day/time
        active_schedule = self._find_active_schedule(area.schedules, current_day_idx, current_time)

        if active_schedule:
            schedule_key = f"{area_id}_{active_schedule.schedule_id}"

            # Only apply if this schedule hasn't been applied yet
            # (to avoid setting temperature every minute)
            if self._last_applied_schedule.get(area_id) != schedule_key:
                await self._apply_schedule(area, active_schedule)
                self._last_applied_schedule[area_id] = schedule_key

        else:
            # No active schedule, clear the tracking
            if area_id in self._last_applied_schedule:
                del self._last_applied_schedule[area_id]
                _LOGGER.debug(
                    "No active schedule for area %s at %s %s",
                    area.name,
                    DAYS_OF_WEEK[current_day_idx],
                    current_time.strftime("%H:%M"),
                )