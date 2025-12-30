"""Sensor management functionality for Area model."""

import logging
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .area import Area  # pragma: no cover

from homeassistant.core import HomeAssistant

from ..const import DEFAULT_PRESENCE_TEMP_BOOST, DEFAULT_WINDOW_OPEN_TEMP_DROP

_LOGGER = logging.getLogger(__name__)


class AreaSensorManager:
    """Manages sensor operations for an Area."""

    def __init__(self, area: "Area") -> None:
        """Initialize sensor manager.

        Args:
            area: The parent Area instance
        """
        self.area = area

    def add_window_sensor(
        self,
        entity_id: str,
        action_when_open: str = "reduce_temperature",
        temp_drop: float | None = None,
    ) -> None:
        """Add a window sensor to the area.

        Args:
            entity_id: Entity ID of the window sensor
            action_when_open: Action to take when window opens (turn_off, reduce_temperature, none)
            temp_drop: Temperature drop when window is open (default: 5.0°C)
        """
        # Check if sensor already exists
        existing = [s for s in self.area.window_sensors if s.get("entity_id") == entity_id]
        if existing:
            _LOGGER.debug(
                "Window sensor %s already exists in area %s", entity_id, self.area.area_id
            )
            return

        sensor_config: dict[str, str | float] = {
            "entity_id": entity_id,
            "action_when_open": action_when_open,
        }
        if action_when_open == "reduce_temperature":
            sensor_config["temp_drop"] = (
                temp_drop if temp_drop is not None else DEFAULT_WINDOW_OPEN_TEMP_DROP
            )

        self.area.window_sensors.append(sensor_config)
        _LOGGER.info(
            "Added window sensor %s to area %s with action %s",
            entity_id,
            self.area.area_id,
            action_when_open,
        )

    def remove_window_sensor(self, entity_id: str) -> None:
        """Remove a window sensor from the area.

        Args:
            entity_id: Entity ID of the sensor to remove
        """
        self.area.window_sensors = [
            s for s in self.area.window_sensors if s.get("entity_id") != entity_id
        ]
        _LOGGER.info("Removed window sensor %s from area %s", entity_id, self.area.area_id)

    def add_presence_sensor(
        self,
        entity_id: str,
    ) -> None:
        """Add a presence sensor to the area.

        Presence sensors control preset mode switching:
        - When away: Switch to "away" preset
        - When home: Switch back to previous preset (typically "home")

        Args:
            entity_id: Entity ID of the presence sensor (person.* or binary_sensor.*)
        """
        # Check if sensor already exists
        existing = [s for s in self.area.presence_sensors if s.get("entity_id") == entity_id]
        if existing:
            _LOGGER.debug(
                "Presence sensor %s already exists in area %s", entity_id, self.area.area_id
            )
            return

        sensor_config = {
            "entity_id": entity_id,
        }

        self.area.presence_sensors.append(sensor_config)
        _LOGGER.info(
            "Added presence sensor %s to area %s (controls preset mode)",
            entity_id,
            self.area.area_id,
        )

    def remove_presence_sensor(self, entity_id: str) -> None:
        """Remove a presence sensor from the area.

        Args:
            entity_id: Entity ID of the sensor to remove
        """
        self.area.presence_sensors = [
            s for s in self.area.presence_sensors if s.get("entity_id") != entity_id
        ]
        _LOGGER.info("Removed presence sensor %s from area %s", entity_id, self.area.area_id)

    def get_window_open_temperature(self) -> Optional[float]:
        """Get temperature when window is open based on sensor actions.

        Returns:
            Temperature or None if no window action applies
        """
        if not self.area.window_is_open or len(self.area.window_sensors) == 0:
            return None

        # Find sensors with action_when_open configured
        for sensor in self.area.window_sensors:
            action = sensor.get("action_when_open", "reduce_temperature")
            if action == "turn_off":
                return 5.0  # Turn off heating (frost protection)
            elif action == "reduce_temperature":
                temp_drop = sensor.get("temp_drop", DEFAULT_WINDOW_OPEN_TEMP_DROP)
                return max(5.0, self.area.target_temperature - temp_drop)
            # "none" action means no temperature change

        return None

    def get_window_open_temperature_with_hass(
        self, hass: HomeAssistant | Any = None, use_global_presence: bool = True
    ) -> Optional[float]:
        """Calculate target temperature when window is open (with hass support).

        If any window sensor reports 'on' (open), applies the configured temp drop.
        If use_global_presence is True and a global presence sensor exists,
        the presence-based temperature is used as the base.

        Args:
            hass: Home Assistant instance (required to check sensor states)
            use_global_presence: Whether to use global presence detection

        Returns:
            Target temperature with window open adjustment, or None if no windows open
        """
        if not hass:
            return self.get_window_open_temperature()

        max_temp_drop = self._get_max_window_temp_drop(hass)
        if max_temp_drop <= 0.0:
            return None

        base_temp = float(self._get_base_temperature_with_presence(use_global_presence))
        return base_temp - max_temp_drop

    def _get_max_window_temp_drop(self, hass: HomeAssistant | Any) -> float:
        """Get the maximum temperature drop from open windows."""
        max_temp_drop = 0.0
        for sensor_config in self.area.window_sensors:
            # sensor_config expected to be a dict with entity_id and settings
            if not sensor_config.get("enabled", True):
                continue
            entity_id = sensor_config.get("entity_id")
            if not entity_id:
                continue
            state = hass.states.get(entity_id)
            if state and state.state == "on":
                temp_drop = sensor_config.get("temp_drop", DEFAULT_WINDOW_OPEN_TEMP_DROP)
                try:
                    temp_drop_val = float(temp_drop)
                except (TypeError, ValueError):
                    temp_drop_val = float(DEFAULT_WINDOW_OPEN_TEMP_DROP)
                max_temp_drop = max(max_temp_drop, temp_drop_val)
        return max_temp_drop

    def _get_base_temperature_with_presence(self, use_global_presence: bool) -> float:
        """Get base temperature, applying presence boost if applicable."""
        base_temp = self.area.target_temperature

        if not use_global_presence or not self.area.area_manager:
            return base_temp

        # If AreaManager provides global presence state helper, use it; otherwise assume no global 'home'
        helper = getattr(self.area.area_manager, "get_global_presence_state", None)
        if callable(helper):
            try:
                if helper() != "home":
                    return base_temp
            except Exception:
                # If the helper fails, fall back to no boost
                _LOGGER.debug(
                    "Failed to get global presence state from AreaManager, skipping boost"
                )
                return base_temp

        # No explicit global presence helper — apply presence boost if any local presence sensors
        return base_temp + self._get_presence_boost()

    def _get_presence_boost(self) -> float:
        """Get the maximum presence boost from enabled sensors."""
        presence_boost = 0.0
        for sensor_config in self.area.presence_sensors:
            if not isinstance(sensor_config, dict):
                continue
            if sensor_config.get("enabled", True):
                boost = sensor_config.get("temp_boost", DEFAULT_PRESENCE_TEMP_BOOST)
                try:
                    boost_val = float(boost)
                except (TypeError, ValueError):
                    boost_val = float(DEFAULT_PRESENCE_TEMP_BOOST)
                presence_boost = max(presence_boost, boost_val)
        return presence_boost
