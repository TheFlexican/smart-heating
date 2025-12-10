"""Sensor platform for Smart Heating integration."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATE_INITIALIZED
from .coordinator import SmartHeatingCoordinator
from .heating_curve import HeatingCurve

_LOGGER = logging.getLogger(__name__)


# noqa: ASYNC109 - Home Assistant platform setup must be async
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Heating sensor platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    _LOGGER.debug("Setting up Smart Heating sensor platform")

    # Get the coordinator from hass.data
    coordinator: SmartHeatingCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensor entities
    entities = [SmartHeatingStatusSensor(coordinator, entry)]

    # Add per-area heating curve and consumption sensors (advanced features opt-in)
    from .area_manager import AreaManager

    area_manager: AreaManager = coordinator.area_manager
    for area in area_manager.get_all_areas().values():
        entities.append(AreaHeatingCurveSensor(coordinator, entry, area))
        entities.append(AreaCurrentConsumptionSensor(coordinator, entry, area))

    # Add entities
    async_add_entities(entities)
    _LOGGER.info("Smart Heating sensor platform setup complete")


class SmartHeatingStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Smart Heating Status Sensor."""

    def __init__(
        self,
        coordinator: SmartHeatingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)

        # Entity attributes
        self._attr_name = "Smart Heating Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_icon = "mdi:radiator"

        _LOGGER.debug(
            "SmartHeatingStatusSensor initialized with unique_id: %s",
            self._attr_unique_id,
        )

    @property
    def native_value(self) -> str:
        """Return the state of the sensor.

        Returns:
            str: The current status
        """
        # Get status from coordinator data
        if self.coordinator.data:
            status = self.coordinator.data.get("status", STATE_INITIALIZED)
            _LOGGER.debug("Sensor state: %s", status)
            return status

        _LOGGER.debug("No coordinator data, returning default state")
        return STATE_INITIALIZED

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes.

        Returns:
            dict: Additional attributes
        """
        attributes = {
            "integration": "smart_heating",
            "version": "2.0.0",
        }

        # Add coordinator data to attributes if available
        if self.coordinator.data:
            attributes["area_count"] = self.coordinator.data.get("area_count", 0)

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available.

        Returns:
            bool: True if the coordinator has data
        """
        return self.coordinator.last_update_success


class AreaHeatingCurveSensor(CoordinatorEntity, SensorEntity):
    """Per-area heating curve sensor - returns calculated flow temp based on heating curve formula."""

    def __init__(self, coordinator: SmartHeatingCoordinator, entry: ConfigEntry, area):
        super().__init__(coordinator)
        self._area = area
        self._attr_name = f"Heating Curve {self._area.name}"
        self._attr_unique_id = f"{entry.entry_id}_heating_curve_{self._area.area_id}"
        self._curve = HeatingCurve(
            heating_system=(
                "underfloor"
                if self._area.heating_type == "floor_heating"
                else "radiator"
            ),
            coefficient=1.0,
        )

    @property
    def native_value(self) -> float | None:
        target = self._area.target_temperature
        outside_temp = None
        if self._area.weather_entity_id:
            state = self.hass.states.get(self._area.weather_entity_id)
            if state and state.state not in ("unavailable", "unknown"):
                try:
                    outside_temp = float(state.state)
                except Exception:
                    outside_temp = None

        if target is None or outside_temp is None:
            return None

        self._curve.update(target, outside_temp)
        return self._curve.value

    @property
    def native_unit_of_measurement(self) -> str:
        return "°C"


class AreaCurrentConsumptionSensor(CoordinatorEntity, SensorEntity):
    """Per-area current consumption/power sensor - estimates based on modulation & configured defaults."""

    def __init__(self, coordinator: SmartHeatingCoordinator, entry: ConfigEntry, area):
        super().__init__(coordinator)
        self._area = area
        self._entry = entry
        self._attr_name = f"Boiler Consumption {self._area.name}"
        self._attr_unique_id = f"{entry.entry_id}_boiler_cons_{self._area.area_id}"

    @property
    def native_value(self) -> float | None:
        # Determine modulation level from configured OpenTherm gateway if present
        from .area_manager import AreaManager

        area_manager: AreaManager = self.coordinator.area_manager
        gateway_id = area_manager.opentherm_gateway_id
        if not gateway_id:
            return None

        state = self.hass.states.get(gateway_id)
        if not state:
            return None
        # Many OT entities expose relative_mod_level or modulation_level attributes
        mod = None
        if "relative_mod_level" in state.attributes:
            try:
                mod = float(state.attributes["relative_mod_level"])
            except Exception:
                mod = None
        elif "modulation_level" in state.attributes:
            try:
                mod = float(state.attributes["modulation_level"])
            except Exception:
                mod = None

        if mod is None:
            return None

        min_cons = area_manager.default_min_consumption or 0.0
        max_cons = area_manager.default_max_consumption or 0.0
        differential = max_cons - min_cons
        return round(min_cons + ((mod / 100.0) * differential), 3)

    @property
    def native_unit_of_measurement(self) -> str:
        return "m³/h"
