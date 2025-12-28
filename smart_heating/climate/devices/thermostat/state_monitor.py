"""Thermostat state monitoring component."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ....models import Area

_LOGGER = logging.getLogger(__name__)


class ThermostatStateMonitor:
    """Monitor thermostat state and activities."""

    def __init__(self, hass: "HomeAssistant"):
        """Initialize state monitor.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    def is_any_thermostat_actively_heating(self, area: "Area") -> bool:
        """Check if any thermostat in the area is actively heating.

        This checks the hvac_action attribute to determine actual heating state.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "heating"
        """
        thermostats = area.get_thermostats()
        for thermostat_id in thermostats:
            state = self.hass.states.get(thermostat_id)
            if state and state.attributes.get("hvac_action") == "heating":
                return True
        return False

    def is_any_thermostat_actively_cooling(self, area: "Area") -> bool:
        """Check if any thermostat in the area is actively cooling.

        This checks the hvac_action attribute to determine actual cooling state.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "cooling"
        """
        thermostats = area.get_thermostats()
        for thermostat_id in thermostats:
            state = self.hass.states.get(thermostat_id)
            if state and state.attributes.get("hvac_action") == "cooling":
                return True
        return False

    def get_thermostat_state(self, thermostat_id: str) -> tuple[str | None, float | None]:
        """Get current HVAC mode and temperature from thermostat state.

        Args:
            thermostat_id: Entity ID of the thermostat

        Returns:
            Tuple of (current_hvac_mode, current_temperature)
        """
        state = self.hass.states.get(thermostat_id)
        if not state:
            return None, None

        current_hvac_mode = state.state
        current_temp = state.attributes.get("temperature")

        return current_hvac_mode, current_temp

    def get_supported_features(self, thermostat_id: str) -> int:
        """Get supported features bitmask for a thermostat.

        Args:
            thermostat_id: Entity ID of the thermostat

        Returns:
            Supported features bitmask, or 0 if state not found
        """
        state = self.hass.states.get(thermostat_id)
        if not state:
            return 0

        return state.attributes.get("supported_features", 0)
