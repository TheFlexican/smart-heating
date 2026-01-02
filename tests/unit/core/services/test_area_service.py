"""Test AreaService."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from smart_heating.core.services.area_service import AreaService
from smart_heating.models import Area


class TestAreaServiceInitialization:
    """Test AreaService initialization."""

    def test_init(self, hass: HomeAssistant):
        """Test service initialization."""
        service = AreaService(hass)

        assert service.hass == hass
        assert service._areas == {}


class TestAreaServiceCreate:
    """Test area creation functionality."""

    def test_add_area(self, hass: HomeAssistant):
        """Test adding an existing area."""
        service = AreaService(hass)
        area = Area(area_id="living_room", name="Living Room", target_temperature=21.0)

        service.add_area(area)

        assert service.area_exists("living_room")
        assert service.get_area("living_room") == area

    def test_add_duplicate_area(self, hass: HomeAssistant):
        """Test adding area with duplicate ID raises error."""
        service = AreaService(hass)
        area1 = Area(area_id="living_room", name="Living Room")
        area2 = Area(area_id="living_room", name="Duplicate")

        service.add_area(area1)

        with pytest.raises(ValueError, match="already exists"):
            service.add_area(area2)

    def test_create_area(self, hass: HomeAssistant):
        """Test creating a new area."""
        service = AreaService(hass)

        area = service.create_area(
            area_id="living_room",
            name="Living Room",
            target_temperature=21.0,
            enabled=True,
        )

        assert area.area_id == "living_room"
        assert area.name == "Living Room"
        assert area.target_temperature == 21.0
        assert area.enabled is True
        assert service.area_exists("living_room")

    def test_create_area_with_defaults(self, hass: HomeAssistant):
        """Test creating area with default values."""
        service = AreaService(hass)

        area = service.create_area(area_id="bedroom", name="Bedroom")

        assert area.area_id == "bedroom"
        assert area.name == "Bedroom"
        assert area.target_temperature == 20.0  # default
        assert area.enabled is True  # default

    def test_create_area_with_kwargs(self, hass: HomeAssistant):
        """Test creating area with additional kwargs."""
        service = AreaService(hass)

        area = service.create_area(
            area_id="office",
            name="Office",
            hidden=True,
            hysteresis_override=1.0,
        )

        assert area.area_id == "office"
        assert area.name == "Office"
        assert area.hidden is True
        assert area.hysteresis_override == 1.0

    def test_create_duplicate_area(self, hass: HomeAssistant):
        """Test creating area with duplicate ID raises error."""
        service = AreaService(hass)
        service.create_area("living_room", "Living Room")

        with pytest.raises(ValueError, match="already exists"):
            service.create_area("living_room", "Duplicate")


class TestAreaServiceGet:
    """Test area retrieval functionality."""

    def test_get_area(self, hass: HomeAssistant):
        """Test getting an area by ID."""
        service = AreaService(hass)
        created_area = service.create_area("living_room", "Living Room")

        retrieved_area = service.get_area("living_room")

        assert retrieved_area == created_area
        assert retrieved_area.area_id == "living_room"

    def test_get_nonexistent_area(self, hass: HomeAssistant):
        """Test getting nonexistent area returns None."""
        service = AreaService(hass)

        assert service.get_area("nonexistent") is None

    def test_get_all_areas(self, hass: HomeAssistant):
        """Test getting all areas."""
        service = AreaService(hass)
        area1 = service.create_area("living_room", "Living Room")
        area2 = service.create_area("bedroom", "Bedroom")

        all_areas = service.get_all_areas()

        assert len(all_areas) == 2
        assert all_areas["living_room"] == area1
        assert all_areas["bedroom"] == area2

    def test_get_all_areas_returns_copy(self, hass: HomeAssistant):
        """Test get_all_areas returns a copy, not the internal dict."""
        service = AreaService(hass)
        service.create_area("living_room", "Living Room")

        areas1 = service.get_all_areas()
        areas2 = service.get_all_areas()

        # Should be equal but not the same object
        assert areas1 == areas2
        assert areas1 is not areas2

    def test_area_exists(self, hass: HomeAssistant):
        """Test checking if area exists."""
        service = AreaService(hass)
        service.create_area("living_room", "Living Room")

        assert service.area_exists("living_room") is True
        assert service.area_exists("nonexistent") is False


class TestAreaServiceUpdate:
    """Test area update functionality."""

    def test_update_area(self, hass: HomeAssistant):
        """Test updating an area."""
        service = AreaService(hass)
        area = service.create_area("living_room", "Living Room", target_temperature=20.0)

        updated_area = service.update_area(
            "living_room",
            target_temperature=22.0,
            enabled=False,
        )

        assert updated_area == area
        assert area.target_temperature == 22.0
        assert area.enabled is False

    def test_update_area_single_field(self, hass: HomeAssistant):
        """Test updating a single field."""
        service = AreaService(hass)
        area = service.create_area("living_room", "Living Room", target_temperature=20.0)

        service.update_area("living_room", name="Living Room Updated")

        assert area.name == "Living Room Updated"
        assert area.target_temperature == 20.0  # unchanged

    def test_update_nonexistent_area(self, hass: HomeAssistant):
        """Test updating nonexistent area returns None."""
        service = AreaService(hass)

        result = service.update_area("nonexistent", target_temperature=22.0)

        assert result is None

    def test_update_area_ignores_invalid_attributes(self, hass: HomeAssistant):
        """Test update ignores attributes that don't exist on Area."""
        service = AreaService(hass)
        area = service.create_area("living_room", "Living Room")

        # Should not raise, just ignore
        service.update_area("living_room", invalid_attribute="value")

        # Area should be unchanged except for valid attributes
        assert not hasattr(area, "invalid_attribute")


class TestAreaServiceDelete:
    """Test area deletion functionality."""

    def test_delete_area(self, hass: HomeAssistant):
        """Test deleting an area."""
        service = AreaService(hass)
        service.create_area("living_room", "Living Room")

        result = service.delete_area("living_room")

        assert result is True
        assert not service.area_exists("living_room")
        assert service.get_area("living_room") is None

    def test_delete_nonexistent_area(self, hass: HomeAssistant):
        """Test deleting nonexistent area returns False."""
        service = AreaService(hass)

        result = service.delete_area("nonexistent")

        assert result is False


class TestAreaServiceLoadAndSerialize:
    """Test area loading and serialization."""

    def test_load_areas(self, hass: HomeAssistant):
        """Test loading areas from data."""
        service = AreaService(hass)
        areas_data = [
            {
                "area_id": "living_room",
                "area_name": "Living Room",
                "target_temperature": 21.0,
                "enabled": True,
                "devices": {},
                "schedules": [],
            },
            {
                "area_id": "bedroom",
                "area_name": "Bedroom",
                "target_temperature": 19.0,
                "enabled": False,
                "devices": {},
                "schedules": [],
            },
        ]

        service.load_areas(areas_data)

        assert len(service.get_all_areas()) == 2
        assert service.area_exists("living_room")
        assert service.area_exists("bedroom")

        living_room = service.get_area("living_room")
        assert living_room.name == "Living Room"
        assert living_room.target_temperature == 21.0
        assert living_room.enabled is True

        bedroom = service.get_area("bedroom")
        assert bedroom.name == "Bedroom"
        assert bedroom.target_temperature == 19.0
        assert bedroom.enabled is False

    def test_load_areas_handles_errors(self, hass: HomeAssistant):
        """Test load_areas handles malformed data gracefully."""
        service = AreaService(hass)
        areas_data = [
            {
                "area_id": "living_room",
                "area_name": "Living Room",
                "target_temperature": 21.0,
                "enabled": True,
                "devices": {},
                "schedules": [],
            },
            {
                # Missing required fields
                "invalid": "data",
            },
            {
                "area_id": "bedroom",
                "area_name": "Bedroom",
                "target_temperature": 19.0,
                "enabled": True,
                "devices": {},
                "schedules": [],
            },
        ]

        service.load_areas(areas_data)

        # Should load valid areas and skip invalid ones
        assert len(service.get_all_areas()) == 2
        assert service.area_exists("living_room")
        assert service.area_exists("bedroom")

    def test_to_dict(self, hass: HomeAssistant):
        """Test serializing areas to dictionaries."""
        service = AreaService(hass)
        service.create_area("living_room", "Living Room", target_temperature=21.0)
        service.create_area("bedroom", "Bedroom", target_temperature=19.0)

        areas_dict = service.to_dict()

        assert isinstance(areas_dict, list)
        assert len(areas_dict) == 2

        # Check that areas are properly serialized
        area_ids = [area["area_id"] for area in areas_dict]
        assert "living_room" in area_ids
        assert "bedroom" in area_ids

    def test_to_dict_empty(self, hass: HomeAssistant):
        """Test serializing empty areas list."""
        service = AreaService(hass)

        areas_dict = service.to_dict()

        assert areas_dict == []


class TestAreaServiceRoundTrip:
    """Test round-trip serialization and loading."""

    def test_round_trip_serialization(self, hass: HomeAssistant):
        """Test that areas can be saved and loaded without data loss."""
        service1 = AreaService(hass)
        service1.create_area("living_room", "Living Room", target_temperature=21.0, enabled=True)
        service1.create_area("bedroom", "Bedroom", target_temperature=19.0, enabled=False)

        # Serialize
        areas_data = service1.to_dict()

        # Create new service and load
        service2 = AreaService(hass)
        service2.load_areas(areas_data)

        # Verify data is preserved
        assert len(service2.get_all_areas()) == 2

        living_room = service2.get_area("living_room")
        assert living_room.name == "Living Room"
        assert living_room.target_temperature == 21.0
        assert living_room.enabled is True

        bedroom = service2.get_area("bedroom")
        assert bedroom.name == "Bedroom"
        assert bedroom.target_temperature == 19.0
        assert bedroom.enabled is False
