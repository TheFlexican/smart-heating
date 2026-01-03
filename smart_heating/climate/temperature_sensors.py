"""Temperature sensor handling for climate control."""

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from homeassistant.core import HomeAssistant

from ..models import Area

if TYPE_CHECKING:
    from ..core.area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


def get_outdoor_temperature_from_weather_entity(
    hass: HomeAssistant, weather_entity_id: str | None
) -> Optional[float]:
    """Get outdoor temperature from a weather entity.

    This is a standalone helper that can be imported by any module.
    For weather entities, temperature is stored in attributes, not state.
    Handles unit conversion (F to C) and invalid states.

    Args:
        hass: Home Assistant instance
        weather_entity_id: Weather entity ID

    Returns:
        Outdoor temperature in Celsius or None if not available
    """
    if not weather_entity_id:
        return None

    state = hass.states.get(weather_entity_id)
    if not state or state.state in ("unknown", "unavailable"):
        return None

    try:
        # For weather entities, temperature is in attributes, not state
        temp = state.attributes.get("temperature")
        if temp is None:
            return None

        temp = float(temp)

        # Check for Fahrenheit and convert to Celsius
        unit = state.attributes.get("unit_of_measurement", "°C")
        if unit in ("°F", "F"):
            temp = (temp - 32) * 5 / 9
            _LOGGER.debug(
                "Converted outdoor temperature from %s: %.1f°F -> %.1f°C",
                weather_entity_id,
                state.attributes.get("temperature"),
                temp,
            )
        return temp
    except (ValueError, TypeError):
        _LOGGER.warning(
            "Invalid temperature from weather entity %s: %s",
            weather_entity_id,
            state.attributes.get("temperature"),
        )
        return None


class TemperatureSensorHandler:
    """Handle temperature sensor readings and conversions."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the temperature sensor handler.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    def convert_fahrenheit_to_celsius(self, temp_fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius.

        Args:
            temp_fahrenheit: Temperature in Fahrenheit

        Returns:
            Temperature in Celsius
        """
        return (temp_fahrenheit - 32) * 5 / 9

    def get_temperature_from_sensor(self, sensor_id: str) -> Optional[float]:
        """Get temperature from a sensor entity.

        Handles unit conversion (F to C) and invalid states.

        Args:
            sensor_id: Sensor entity ID

        Returns:
            Temperature in Celsius or None if unavailable
        """
        state = self.hass.states.get(sensor_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None

        try:
            temp_value = float(state.state)

            # Check if temperature is in Fahrenheit and convert to Celsius
            unit = state.attributes.get("unit_of_measurement", "°C")
            if unit in ("°F", "F"):
                temp_value = self.convert_fahrenheit_to_celsius(temp_value)
                _LOGGER.debug(
                    "Converted temperature from %s: %s°F -> %.1f°C",
                    sensor_id,
                    state.state,
                    temp_value,
                )

            return temp_value
        except (ValueError, TypeError):
            _LOGGER.warning("Invalid temperature from %s: %s", sensor_id, state.state)
            return None

    def get_temperature_from_thermostat(self, thermostat_id: str) -> Optional[float]:
        """Get current temperature from a thermostat entity.

        Handles unit conversion (F to C) and invalid states.

        Args:
            thermostat_id: Thermostat entity ID

        Returns:
            Temperature in Celsius or None if unavailable
        """
        state = self.hass.states.get(thermostat_id)
        if not state:
            _LOGGER.debug(
                "Thermostat %s not found in state registry",
                thermostat_id,
            )
            return None

        if state.state in ("unknown", "unavailable"):
            _LOGGER.debug(
                "Thermostat %s state is %s",
                thermostat_id,
                state.state,
            )
            return None

        current_temp = state.attributes.get("current_temperature")
        if current_temp is None:
            _LOGGER.debug(
                "Thermostat %s has no current_temperature attribute (state=%s, attributes=%s)",
                thermostat_id,
                state.state,
                list(state.attributes.keys()),
            )
            return None

        try:
            temp_value = float(current_temp)

            # Check if temperature is in Fahrenheit and convert to Celsius
            unit = state.attributes.get("unit_of_measurement", "°C")
            if unit in ("°F", "F"):
                temp_value = self.convert_fahrenheit_to_celsius(temp_value)
                _LOGGER.debug(
                    "Converted temperature from thermostat %s: %.1f°F -> %.1f°C",
                    thermostat_id,
                    current_temp,
                    temp_value,
                )

            return temp_value
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid current_temperature from thermostat %s: %s",
                thermostat_id,
                current_temp,
            )
            return None

    def collect_area_temperatures(self, area: Area) -> list[float]:
        """Collect all temperature readings for an area.

        If a primary_temperature_sensor is set, only use that device.
        Otherwise, collect from all temperature sensors and thermostats.

        Args:
            area: Area instance

        Returns:
            List of temperature values in Celsius
        """
        temps = []

        # If primary temperature sensor is configured, use only that
        if area.primary_temperature_sensor:
            # Try as temperature sensor first
            temp = self.get_temperature_from_sensor(area.primary_temperature_sensor)
            if temp is not None:
                return [temp]

            # Try as thermostat
            temp = self.get_temperature_from_thermostat(area.primary_temperature_sensor)
            if temp is not None:
                return [temp]

            _LOGGER.debug(
                "Primary temperature sensor %s unavailable for area %s, falling back to all sensors",
                area.primary_temperature_sensor,
                area.area_id,
            )

        # No primary sensor or primary sensor unavailable - collect from all
        # Read from temperature sensors
        for sensor_id in area.get_temperature_sensors():
            temp = self.get_temperature_from_sensor(sensor_id)
            if temp is not None:
                temps.append(temp)

        # Read from thermostats
        thermostat_list = area.get_thermostats()
        _LOGGER.debug(
            "Checking %d thermostats for area %s: %s",
            len(thermostat_list),
            area.area_id,
            thermostat_list,
        )
        for thermostat_id in thermostat_list:
            temp = self.get_temperature_from_thermostat(thermostat_id)
            if temp is not None:
                temps.append(temp)
                _LOGGER.debug(
                    "Got temperature %.1f°C from thermostat %s for area %s",
                    temp,
                    thermostat_id,
                    area.area_id,
                )

        return temps

    async def async_get_outdoor_temperature(self, area: Area) -> Optional[float]:
        """Get outdoor temperature from weather entity.

        Delegates to standalone helper function for consistent behavior.

        Args:
            area: Area instance (checks weather_entity_id)

        Returns:
            Outdoor temperature in Celsius or None if not available
        """
        await asyncio.sleep(0)  # Ensure this is an async function
        return get_outdoor_temperature_from_weather_entity(
            self.hass, area.boost_manager.weather_entity_id
        )

    def update_all_area_temperatures(self, area_manager: "AreaManager") -> None:
        """Update current temperatures for all areas from sensors.

        Collects temperatures from sensors and thermostats for each area,
        calculates the average, and updates the area's current_temperature attribute.

        Args:
            area_manager: Area manager instance with areas to update
        """
        for area_id, area in area_manager.get_all_areas().items():
            temp_sensors = area.get_temperature_sensors()
            thermostats = area.get_thermostats()

            if not temp_sensors and not thermostats:
                continue

            temps = self.collect_area_temperatures(area)

            if temps:
                avg_temp = sum(temps) / len(temps)
                area.current_temperature = avg_temp
                _LOGGER.debug(
                    "Area %s temperature: %.1f°C (from %d sensors)",
                    area_id,
                    avg_temp,
                    len(temps),
                )
