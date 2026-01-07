"""Boost mode manager for heating areas."""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from .area import Area

_LOGGER = logging.getLogger(__name__)


class AreaBoostManager:
    """Manages boost mode functionality for an area.

    Handles:
    - Regular boost mode
    - Night boost
    - Smart boost
    - Boost calculations and state management
    """

    def __init__(self, area: "Area") -> None:
        """Initialize boost manager.

        Args:
            area: Parent area instance
        """
        self.area = area

        # Regular boost state
        self.boost_mode_active: bool = False
        self.boost_duration: int = 60  # minutes
        self.boost_temp: float = 25.0
        self.boost_end_time: datetime | None = None

        # Night boost settings
        self.night_boost_enabled: bool = False  # Disabled by default to avoid surprises
        self.night_boost_offset: float = 0.5  # Add 0.5°C during night hours
        self.night_boost_start_time: str = "22:00"
        self.night_boost_end_time: str = "06:00"

        # Smart boost settings (AI-powered predictive heating)
        self.smart_boost_enabled: bool = False
        self.smart_boost_target_time: str = "06:00"  # Time when room should be at target temp
        self.weather_entity_id: str | None = None  # Outdoor temperature sensor

        # Smart boost runtime state (not persisted)
        self.smart_boost_active: bool = False  # Currently in smart boost heating period
        self.smart_boost_original_target: float | None = None  # Original target before smart boost

        # Proactive temperature maintenance settings
        self.proactive_maintenance_enabled: bool = False  # Master toggle
        self.proactive_maintenance_sensitivity: float = 1.0  # 0.5-2.0 multiplier for margin
        self.proactive_maintenance_min_trend: float = -0.1  # Min trend (°C/hour) to trigger
        self.proactive_maintenance_margin_minutes: int = 5  # Extra buffer (15 for floor heating)
        self.proactive_maintenance_cooldown_minutes: int = 10  # Prevent oscillation

        # Proactive maintenance runtime state (not persisted)
        self.proactive_maintenance_active: bool = False  # Currently in proactive heating
        self.proactive_maintenance_started_at: datetime | None = None
        self.proactive_maintenance_ended_at: datetime | None = None

    def activate_boost(self, duration: int, temp: float | None = None) -> None:
        """Activate boost mode for a specified duration.

        Args:
            duration: Duration in minutes
            temp: Optional boost temperature (defaults to current boost_temp)
        """
        from ..const import PRESET_BOOST

        self.boost_mode_active = True
        self.boost_duration = duration
        self.boost_end_time = dt_util.now() + timedelta(minutes=duration)
        self.area.preset_mode = PRESET_BOOST

        if temp is not None:
            self.boost_temp = temp

        _LOGGER.info(
            "Boost mode activated for area %s: %.1f°C for %d minutes",
            self.area.area_id,
            self.boost_temp,
            duration,
        )

    def cancel_boost(self) -> None:
        """Cancel active boost mode."""
        from ..const import PRESET_NONE

        if self.boost_mode_active:
            self.boost_mode_active = False
            self.boost_end_time = None
            self.area.preset_mode = PRESET_NONE
            _LOGGER.info("Boost mode cancelled for area %s", self.area.area_id)

    def is_boost_active(self) -> bool:
        """Check if boost is currently active.

        Returns:
            True if boost is active and not expired
        """
        if not self.boost_mode_active:
            return False

        # Check if boost has expired (handle naive stored end times)
        if self.boost_end_time:
            boost_end = self.boost_end_time
            if boost_end.tzinfo is None:
                boost_end = dt_util.as_utc(boost_end)
            if dt_util.now() >= boost_end:
                self.cancel_boost()
                return False

        return True

    def check_boost_expiry(self) -> bool:
        """Check if boost mode has expired and cancel if needed.

        Returns:
            True if boost was cancelled, False otherwise
        """
        if not self.boost_mode_active or not self.boost_end_time:
            return False

        # Compare with timezone-aware end time if necessary
        boost_end = self.boost_end_time
        if boost_end.tzinfo is None:
            boost_end = dt_util.as_utc(boost_end)
        if dt_util.now() >= boost_end:
            self.cancel_boost()
            return True

        return False

    def is_night_boost_active(self, current_time: datetime | None = None) -> bool:
        """Check if night boost is active.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if night boost is active
        """
        if not self.night_boost_enabled:
            return False

        if current_time is None:
            current_time = dt_util.now()

        # Validate time period
        if self.night_boost_start_time == self.night_boost_end_time:
            _LOGGER.warning(
                "Night boost disabled for %s: start_time equals end_time", self.area.area_id
            )
            return False

        # Skip regular night boost if smart boost is active (smart boost has priority)
        if self.smart_boost_active:
            _LOGGER.debug("Night boost skipped for %s: Smart boost is active", self.area.area_id)
            return False

        # Check if current time is within night boost period
        return self._is_in_time_period(
            current_time, self.night_boost_start_time, self.night_boost_end_time
        )

    def _is_in_time_period(
        self, current_time: datetime, start_time_str: str, end_time_str: str
    ) -> bool:
        """Check if current time is within a time period.

        Handles periods that cross midnight.

        Args:
            current_time: Current datetime
            start_time_str: Start time as "HH:MM"
            end_time_str: End time as "HH:MM"

        Returns:
            True if current time is in period
        """
        start_hour, start_min = map(int, start_time_str.split(":"))
        end_hour, end_min = map(int, end_time_str.split(":"))
        current_hour = current_time.hour
        current_min = current_time.minute

        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        current_minutes = current_hour * 60 + current_min

        if start_minutes <= end_minutes:
            # Normal period (e.g., 08:00-18:00)
            return start_minutes <= current_minutes < end_minutes
        else:
            # Period crosses midnight (e.g., 22:00-06:00)
            return current_minutes >= start_minutes or current_minutes < end_minutes

    def get_night_boost_offset(self, current_time: datetime | None = None) -> float:
        """Get temperature offset from night boost if active.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            Temperature offset in °C (0.0 if not active)
        """
        if self.is_night_boost_active(current_time):
            return self.night_boost_offset
        return 0.0

    def apply_night_boost(self, target: float, current_time: datetime | None = None) -> float:
        """Apply night boost to target temperature if applicable.

        Night boost adds a small temperature offset during configured hours to
        pre-heat the space before the morning schedule. It works additively on
        top of any active schedule (e.g., sleep preset).

        Smart boost takes priority - if smart boost is active, regular night boost is skipped.

        Args:
            target: Current target temperature
            current_time: Current time (defaults to now)

        Returns:
            Adjusted temperature with night boost
        """
        if current_time is None:
            current_time = dt_util.now()

        if not self.is_night_boost_active(current_time):
            _LOGGER.debug(
                "Night boost inactive for %s at %02d:%02d (period: %s-%s)",
                self.area.area_id,
                current_time.hour,
                current_time.minute,
                self.night_boost_start_time,
                self.night_boost_end_time,
            )
            return target

        old_target = target
        target += self.night_boost_offset
        _LOGGER.info(
            "Night boost active for %s (%s-%s): %.1f°C + %.1f°C = %.1f°C",
            self.area.area_id,
            self.night_boost_start_time,
            self.night_boost_end_time,
            old_target,
            self.night_boost_offset,
            target,
        )

        # Log to area logger if available
        if self.area.area_manager and hasattr(self.area.area_manager, "hass"):
            area_logger = self.area.area_manager.hass.data.get("smart_heating", {}).get(
                "area_logger"
            )
            if area_logger:
                area_logger.log_event(
                    self.area.area_id,
                    "temperature",
                    f"Night boost applied: +{self.night_boost_offset}°C",
                    {
                        "base_target": old_target,
                        "boost_offset": self.night_boost_offset,
                        "effective_target": target,
                        "boost_period": f"{self.night_boost_start_time}-{self.night_boost_end_time}",
                        "current_time": f"{current_time.hour:02d}:{current_time.minute:02d}",
                    },
                )

        return target

    def start_proactive_maintenance(self) -> None:
        """Start proactive temperature maintenance.

        Called when the system predicts a temperature drop and starts heating preemptively.
        """
        self.proactive_maintenance_active = True
        self.proactive_maintenance_started_at = dt_util.now()
        _LOGGER.info(
            "Proactive maintenance started for area %s",
            self.area.area_id,
        )

    def end_proactive_maintenance(self) -> None:
        """End proactive maintenance maintenance.

        Called when target temperature is reached or conditions change.
        """
        if self.proactive_maintenance_active:
            self.proactive_maintenance_active = False
            self.proactive_maintenance_ended_at = dt_util.now()
            _LOGGER.info(
                "Proactive maintenance ended for area %s",
                self.area.area_id,
            )

    def is_proactive_cooldown_active(self, current_time: datetime | None = None) -> bool:
        """Check if proactive maintenance cooldown is active.

        Prevents rapid cycling by ensuring a minimum time between proactive heating sessions.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if cooldown is active (should not start proactive heating)
        """
        if not self.proactive_maintenance_ended_at:
            return False

        if current_time is None:
            current_time = dt_util.now()

        cooldown_end = self.proactive_maintenance_ended_at + timedelta(
            minutes=self.proactive_maintenance_cooldown_minutes
        )
        return current_time < cooldown_end

    def get_effective_margin_minutes(self) -> int:
        """Get effective margin in minutes, considering heating type.

        Floor heating systems use a larger margin due to thermal inertia.

        Returns:
            Margin in minutes (adjusted for heating type)
        """
        base_margin = self.proactive_maintenance_margin_minutes

        # Floor heating needs larger margin due to slow thermal response
        if hasattr(self.area, "heating_type") and self.area.heating_type == "floor_heating":
            return max(base_margin, 15)  # Minimum 15 minutes for floor heating

        return base_margin

    def to_dict(self) -> dict[str, Any]:
        """Serialize boost configuration.

        Returns:
            Boost configuration dictionary
        """
        return {
            # Regular boost
            "boost_mode_active": self.boost_mode_active,
            "boost_duration": self.boost_duration,
            "boost_temp": self.boost_temp,
            "boost_end_time": (self.boost_end_time.isoformat() if self.boost_end_time else None),
            # Night boost
            "night_boost_enabled": self.night_boost_enabled,
            "night_boost_offset": self.night_boost_offset,
            "night_boost_start_time": self.night_boost_start_time,
            "night_boost_end_time": self.night_boost_end_time,
            # Smart boost
            "smart_boost_enabled": self.smart_boost_enabled,
            "smart_boost_target_time": self.smart_boost_target_time,
            "weather_entity_id": self.weather_entity_id,
            # Proactive maintenance
            "proactive_maintenance_enabled": self.proactive_maintenance_enabled,
            "proactive_maintenance_sensitivity": self.proactive_maintenance_sensitivity,
            "proactive_maintenance_min_trend": self.proactive_maintenance_min_trend,
            "proactive_maintenance_margin_minutes": self.proactive_maintenance_margin_minutes,
            "proactive_maintenance_cooldown_minutes": self.proactive_maintenance_cooldown_minutes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], area: "Area") -> "AreaBoostManager":
        """Deserialize boost configuration.

        Args:
            data: Configuration dictionary
            area: Parent area

        Returns:
            AreaBoostManager instance
        """
        from ..const import (
            DEFAULT_NIGHT_BOOST_END_TIME,
            DEFAULT_NIGHT_BOOST_START_TIME,
        )

        manager = cls(area)

        # Regular boost
        manager.boost_mode_active = data.get("boost_mode_active", False)
        manager.boost_duration = data.get("boost_duration", 60)
        manager.boost_temp = data.get("boost_temp", 25.0)

        boost_end_time_str = data.get("boost_end_time")
        if boost_end_time_str:
            manager.boost_end_time = datetime.fromisoformat(boost_end_time_str)

        # Night boost
        manager.night_boost_enabled = data.get("night_boost_enabled", False)
        manager.night_boost_offset = data.get("night_boost_offset", 0.5)
        manager.night_boost_start_time = data.get(
            "night_boost_start_time", DEFAULT_NIGHT_BOOST_START_TIME
        )
        manager.night_boost_end_time = data.get(
            "night_boost_end_time", DEFAULT_NIGHT_BOOST_END_TIME
        )

        # Smart boost
        manager.smart_boost_enabled = data.get("smart_boost_enabled", False)
        manager.smart_boost_target_time = data.get("smart_boost_target_time", "06:00")
        manager.weather_entity_id = data.get("weather_entity_id")

        # Proactive maintenance
        manager.proactive_maintenance_enabled = data.get("proactive_maintenance_enabled", False)
        manager.proactive_maintenance_sensitivity = data.get(
            "proactive_maintenance_sensitivity", 1.0
        )
        manager.proactive_maintenance_min_trend = data.get("proactive_maintenance_min_trend", -0.1)
        manager.proactive_maintenance_margin_minutes = data.get(
            "proactive_maintenance_margin_minutes", 5
        )
        manager.proactive_maintenance_cooldown_minutes = data.get(
            "proactive_maintenance_cooldown_minutes", 10
        )

        return manager
