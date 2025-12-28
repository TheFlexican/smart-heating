"""Schedule management functionality for Area model."""

import logging
from datetime import datetime

from ..const import (
    PRESET_BOOST,
    PRESET_NONE,
)
from .schedule import Schedule

_LOGGER = logging.getLogger(__name__)


class AreaScheduleManager:
    """Manages schedule operations for an Area."""

    def __init__(self, area: "Area") -> None:
        """Initialize schedule manager.

        Args:
            area: The parent Area instance
        """
        self.area = area

    def add_schedule(self, schedule: Schedule) -> None:
        """Add a schedule to the area.

        Args:
            schedule: Schedule instance
        """
        self.area.schedules[schedule.schedule_id] = schedule
        _LOGGER.debug("Added schedule %s to area %s", schedule.schedule_id, self.area.area_id)

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule from the area.

        Args:
            schedule_id: Schedule identifier
        """
        if schedule_id in self.area.schedules:
            del self.area.schedules[schedule_id]
            _LOGGER.debug("Removed schedule %s from area %s", schedule_id, self.area.area_id)

    def get_active_schedule_temperature(self, current_time: datetime | None = None) -> float | None:
        """Get the temperature from the currently active schedule.

        Args:
            current_time: Current time (defaults to now)

        Returns:
            Temperature from active schedule or None
        """
        if current_time is None:
            current_time = datetime.now()

        # Find all active schedules and get the latest one
        active_schedules = [s for s in self.area.schedules.values() if s.is_active(current_time)]

        if not active_schedules:
            return None

        # Sort by time and get the latest
        active_schedules.sort(key=lambda s: s.time, reverse=True)
        return active_schedules[0].temperature

    def get_base_target_from_preset_or_schedule(self, current_time: datetime) -> tuple[float, str]:
        """Get base target temperature from preset or schedule.

        Args:
            current_time: Current time

        Returns:
            Tuple of (temperature, source_description)
        """
        # Priority 1: Preset mode temperature
        if self.area.preset_mode != PRESET_NONE and self.area.preset_mode != PRESET_BOOST:
            # Use preset manager to get temperature
            if hasattr(self.area, "preset_manager"):
                target = self.area.preset_manager.get_preset_temperature()
            else:
                # Fallback to direct method call
                target = self.area.get_preset_temperature()
            source = f"preset:{self.area.preset_mode}"
            return target, source

        # Priority 2: Schedule temperature (if available)
        target = self.get_active_schedule_temperature(current_time)
        if target is not None:
            return target, "schedule"

        # Priority 3: Base target temperature
        return self.area.target_temperature, "base_target"

    def apply_night_boost(self, target: float, current_time: datetime) -> float:
        """Apply night boost to target temperature if applicable.

        Delegates to the area's boost_manager.

        Args:
            target: Current target temperature
            current_time: Current time

        Returns:
            Adjusted temperature with night boost
        """
        return self.area.boost_manager.apply_night_boost(target, current_time)

    def get_effective_target_temperature(self, current_time: datetime | None = None) -> float:
        """Get the effective target temperature considering all factors.

        Priority order:
        1. Boost mode (if active)
        2. Window open (reduce temperature)
        3. Preset mode temperature
        4. Schedule temperature
        5. Base target temperature
        6. Night boost adjustment
        7. Presence boost (if detected)

        Args:
            current_time: Current time (defaults to now)

        Returns:
            Effective target temperature
        """
        if current_time is None:
            current_time = datetime.now()

        # Check if boost mode has expired
        if hasattr(self.area, "preset_manager"):
            self.area.preset_manager.check_boost_expiry()
        else:
            self.area.check_boost_expiry()

        # Priority 1: Boost mode
        if self.area.boost_manager.boost_mode_active:
            return self.area.boost_manager.boost_temp

        # Priority 2: Window open actions
        window_temp = self.area.sensor_manager.get_window_open_temperature()
        if window_temp is not None:
            return window_temp

        # Priority 3-5: Get base target from preset or schedule
        target, source = self.get_base_target_from_preset_or_schedule(current_time)

        # Log what we're starting with for debugging
        _LOGGER.debug(
            "Effective temp calculation for %s: source=%s, target=%.1f°C",
            self.area.area_id,
            source,
            target,
        )

        # Priority 6: Apply night boost if enabled (additive)
        target = self.apply_night_boost(target, current_time)

        # Note: Presence sensor actions are now handled by switching preset modes
        # (see climate_controller.py) rather than adjusting temperature directly

        return target
