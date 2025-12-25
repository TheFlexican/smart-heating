"""Preset management functionality for Area model."""

import logging
from datetime import datetime, timedelta

from ..const import (
    DEFAULT_ACTIVITY_TEMP,
    DEFAULT_AWAY_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_SLEEP_TEMP,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_NONE,
    PRESET_SLEEP,
)

_LOGGER = logging.getLogger(__name__)


class AreaPresetManager:
    """Manages preset operations for an Area."""

    def __init__(self, area: "Area") -> None:
        """Initialize preset manager.

        Args:
            area: The parent Area instance
        """
        self.area = area

    def get_preset_temperature(self) -> float:
        """Get the temperature for the current preset mode.

        Returns:
            Temperature for the active preset, or current target if no preset active
        """
        if self.area.preset_mode == PRESET_NONE:
            return self.area.target_temperature

        # Map preset modes to their temperature settings
        preset_temps = {
            PRESET_AWAY: self._get_away_temp(),
            PRESET_ECO: self._get_eco_temp(),
            PRESET_COMFORT: self._get_comfort_temp(),
            PRESET_HOME: self._get_home_temp(),
            PRESET_SLEEP: self._get_sleep_temp(),
            PRESET_ACTIVITY: self._get_activity_temp(),
        }

        return preset_temps.get(self.area.preset_mode, self.area.target_temperature)

    def _get_away_temp(self) -> float:
        """Get away temperature (global or custom)."""
        if self.area.use_global_away and self.area.area_manager:
            return self.area.area_manager.global_away_temp
        return self.area.away_temp or DEFAULT_AWAY_TEMP

    def _get_eco_temp(self) -> float:
        """Get eco temperature (global or custom)."""
        if self.area.use_global_eco and self.area.area_manager:
            return self.area.area_manager.global_eco_temp
        return self.area.eco_temp or DEFAULT_ECO_TEMP

    def _get_comfort_temp(self) -> float:
        """Get comfort temperature (global or custom)."""
        if self.area.use_global_comfort and self.area.area_manager:
            return self.area.area_manager.global_comfort_temp
        return self.area.comfort_temp or DEFAULT_COMFORT_TEMP

    def _get_home_temp(self) -> float:
        """Get home temperature (global or custom)."""
        if self.area.use_global_home and self.area.area_manager:
            return self.area.area_manager.global_home_temp
        return self.area.home_temp or DEFAULT_HOME_TEMP

    def _get_sleep_temp(self) -> float:
        """Get sleep temperature (global or custom)."""
        if self.area.use_global_sleep and self.area.area_manager:
            return self.area.area_manager.global_sleep_temp
        return self.area.sleep_temp or DEFAULT_SLEEP_TEMP

    def _get_activity_temp(self) -> float:
        """Get activity temperature (global or custom)."""
        if self.area.use_global_activity and self.area.area_manager:
            return self.area.area_manager.global_activity_temp
        return self.area.activity_temp or DEFAULT_ACTIVITY_TEMP

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode for this area.

        Args:
            preset_mode: Preset mode to set
        """
        self.area.preset_mode = preset_mode
        _LOGGER.info("Area %s preset mode set to %s", self.area.area_id, preset_mode)

        # If boost mode was active, cancel it when changing presets
        if preset_mode != PRESET_BOOST and self.area.boost_mode_active:
            self.cancel_boost_mode()

    def set_boost_mode(self, duration: int, temp: float | None = None) -> None:
        """Enable boost mode for a specified duration.

        Args:
            duration: Duration in minutes
            temp: Optional boost temperature (defaults to current target + 2.0°C)
        """
        self.area.boost_mode_active = True
        self.area.boost_duration = duration
        self.area.boost_end_time = datetime.now() + timedelta(minutes=duration)
        self.area.preset_mode = PRESET_BOOST

        if temp is not None:
            self.area.boost_temp = temp

        _LOGGER.info(
            "Boost mode activated for area %s: %.1f°C for %d minutes",
            self.area.area_id,
            self.area.boost_temp,
            duration,
        )

    def cancel_boost_mode(self) -> None:
        """Cancel boost mode."""
        if self.area.boost_mode_active:
            self.area.boost_mode_active = False
            self.area.boost_end_time = None
            self.area.preset_mode = PRESET_NONE
            _LOGGER.info("Boost mode cancelled for area %s", self.area.area_id)

    def check_boost_expiry(self) -> bool:
        """Check if boost mode has expired.

        Returns:
            True if boost mode expired and was cancelled
        """
        if not self.area.boost_mode_active or not self.area.boost_end_time:
            return False

        if datetime.now() >= self.area.boost_end_time:
            self.cancel_boost_mode()
            return True

        return False
