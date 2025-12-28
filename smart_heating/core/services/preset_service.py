"""Global preset temperature management service."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from ...const import (
    DEFAULT_ACTIVITY_TEMP,
    DEFAULT_AWAY_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_SLEEP_TEMP,
)

_LOGGER = logging.getLogger(__name__)


class PresetService:
    """Handles global preset temperature management."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize preset service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

        # Global Preset Temperatures
        self.global_away_temp: float = DEFAULT_AWAY_TEMP
        self.global_eco_temp: float = DEFAULT_ECO_TEMP
        self.global_comfort_temp: float = DEFAULT_COMFORT_TEMP
        self.global_home_temp: float = DEFAULT_HOME_TEMP
        self.global_sleep_temp: float = DEFAULT_SLEEP_TEMP
        self.global_activity_temp: float = DEFAULT_ACTIVITY_TEMP

    def set_preset_temperature(self, preset_name: str, temperature: float) -> None:
        """Set a global preset temperature.

        Args:
            preset_name: Name of the preset (away, eco, comfort, home, sleep, activity)
            temperature: Temperature value

        Raises:
            ValueError: If preset name is invalid
        """
        preset_attr = f"global_{preset_name}_temp"
        if not hasattr(self, preset_attr):
            raise ValueError(f"Invalid preset name: {preset_name}")

        setattr(self, preset_attr, temperature)
        _LOGGER.info("Set global %s temperature to %.1f°C", preset_name, temperature)

    def get_preset_temperature(self, preset_name: str) -> float:
        """Get a global preset temperature.

        Args:
            preset_name: Name of the preset (away, eco, comfort, home, sleep, activity)

        Returns:
            Temperature value

        Raises:
            ValueError: If preset name is invalid
        """
        preset_attr = f"global_{preset_name}_temp"
        if not hasattr(self, preset_attr):
            raise ValueError(f"Invalid preset name: {preset_name}")

        return getattr(self, preset_attr)

    def get_all_presets(self) -> dict[str, float]:
        """Get all global preset temperatures.

        Returns:
            Dictionary of preset_name -> temperature
        """
        return {
            "away": self.global_away_temp,
            "eco": self.global_eco_temp,
            "comfort": self.global_comfort_temp,
            "home": self.global_home_temp,
            "sleep": self.global_sleep_temp,
            "activity": self.global_activity_temp,
        }

    def load_presets(self, data: dict[str, Any]) -> None:
        """Load preset temperatures from data.

        Args:
            data: Configuration dictionary
        """
        self.global_away_temp = data.get("global_away_temp", DEFAULT_AWAY_TEMP)
        self.global_eco_temp = data.get("global_eco_temp", DEFAULT_ECO_TEMP)
        self.global_comfort_temp = data.get("global_comfort_temp", DEFAULT_COMFORT_TEMP)
        self.global_home_temp = data.get("global_home_temp", DEFAULT_HOME_TEMP)
        self.global_sleep_temp = data.get("global_sleep_temp", DEFAULT_SLEEP_TEMP)
        self.global_activity_temp = data.get("global_activity_temp", DEFAULT_ACTIVITY_TEMP)
        _LOGGER.debug("Loaded global preset temperatures")

    def to_dict(self) -> dict[str, float]:
        """Serialize preset temperatures to dictionary.

        Returns:
            Dictionary of preset configuration
        """
        return {
            "global_away_temp": self.global_away_temp,
            "global_eco_temp": self.global_eco_temp,
            "global_comfort_temp": self.global_comfort_temp,
            "global_home_temp": self.global_home_temp,
            "global_sleep_temp": self.global_sleep_temp,
            "global_activity_temp": self.global_activity_temp,
        }
