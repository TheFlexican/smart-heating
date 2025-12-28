"""Area CRUD operations service."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ...exceptions import SmartHeatingError, ValidationError
from ...models import Area

_LOGGER = logging.getLogger(__name__)


class AreaService:
    """Handles area CRUD operations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize area service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._areas: dict[str, Area] = {}

    def add_area(self, area: Area) -> None:
        """Add an existing area to the service.

        Args:
            area: Area instance to add

        Raises:
            ValueError: If area_id already exists
        """
        if area.area_id in self._areas:
            raise ValueError(f"Area {area.area_id} already exists")

        self._areas[area.area_id] = area
        _LOGGER.info("Added area: %s (%s)", area.area_id, area.name)

    def create_area(
        self,
        area_id: str,
        name: str,
        target_temperature: float = 20.0,
        enabled: bool = True,
        **kwargs: Any,
    ) -> Area:
        """Create a new area.

        Args:
            area_id: Unique identifier for the area
            name: Display name for the area
            target_temperature: Initial target temperature
            enabled: Whether area is enabled
            **kwargs: Additional area parameters

        Returns:
            Created Area instance

        Raises:
            ValueError: If area_id already exists
        """
        if area_id in self._areas:
            raise ValueError(f"Area {area_id} already exists")

        area = Area(
            area_id=area_id,
            name=name,
            target_temperature=target_temperature,
            enabled=enabled,
        )

        # Set additional properties
        for key, value in kwargs.items():
            if hasattr(area, key):
                setattr(area, key, value)

        self._areas[area.area_id] = area
        _LOGGER.info("Created area: %s (%s)", area_id, name)

        return area

    def get_area(self, area_id: str) -> Area | None:
        """Get area by ID.

        Args:
            area_id: Area identifier

        Returns:
            Area instance or None if not found
        """
        return self._areas.get(area_id)

    def get_all_areas(self) -> dict[str, Area]:
        """Get all areas.

        Returns:
            Dictionary of area_id -> Area
        """
        return self._areas.copy()

    def update_area(self, area_id: str, **updates: Any) -> Area | None:
        """Update area settings.

        Args:
            area_id: Area identifier
            **updates: Fields to update

        Returns:
            Updated Area instance or None if not found
        """
        area = self._areas.get(area_id)
        if not area:
            _LOGGER.warning("Area not found: %s", area_id)
            return None

        for key, value in updates.items():
            if hasattr(area, key):
                setattr(area, key, value)
                _LOGGER.debug("Updated %s.%s = %s", area_id, key, value)

        return area

    def delete_area(self, area_id: str) -> bool:
        """Delete an area.

        Args:
            area_id: Area identifier

        Returns:
            True if deleted, False if not found
        """
        if area_id in self._areas:
            del self._areas[area_id]
            _LOGGER.info("Deleted area: %s", area_id)
            return True

        _LOGGER.warning("Cannot delete - area not found: %s", area_id)
        return False

    def area_exists(self, area_id: str) -> bool:
        """Check if area exists.

        Args:
            area_id: Area identifier

        Returns:
            True if area exists
        """
        return area_id in self._areas

    def load_areas(self, areas_data: list[dict]) -> None:
        """Load areas from data.

        Args:
            areas_data: List of area configuration dictionaries
        """
        for area_data in areas_data:
            try:
                area = Area.from_dict(area_data)
                self._areas[area.area_id] = area
                _LOGGER.debug("Loaded area: %s", area.area_id)
            except (
                HomeAssistantError,
                SmartHeatingError,
                ValidationError,
                AttributeError,
                KeyError,
            ) as e:
                _LOGGER.error("Failed to load area: %s", e, exc_info=True)

    def to_dict(self) -> list[dict]:
        """Serialize all areas to dictionaries.

        Returns:
            List of area configuration dictionaries
        """
        return [area.to_dict() for area in self._areas.values()]

    def update_area_temperature(self, area_id: str, temperature: float) -> None:
        """Update the current temperature of an area.

        Args:
            area_id: Area identifier
            temperature: New temperature value

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.current_temperature = temperature
        _LOGGER.debug("Updated area %s temperature to %.1f°C", area_id, temperature)

    def set_area_target_temperature(self, area_id: str, temperature: float) -> None:
        """Set the target temperature of an area.

        Args:
            area_id: Area identifier
            temperature: Target temperature

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        old_temp = area.target_temperature
        area.target_temperature = temperature
        _LOGGER.info(
            "TARGET TEMP CHANGE for %s: %.1f°C → %.1f°C (preset: %s)",
            area_id,
            old_temp,
            temperature,
            area.preset_mode,
        )

    def enable_area(self, area_id: str) -> None:
        """Enable an area.

        Args:
            area_id: Area identifier

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.enabled = True
        _LOGGER.info("Enabled area %s", area_id)

    def disable_area(self, area_id: str) -> None:
        """Disable an area.

        Args:
            area_id: Area identifier

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.enabled = False
        _LOGGER.info("Disabled area %s", area_id)
