"""Unit tests for heating type feature."""

from smart_heating.models.area import Area


class TestHeatingType:
    """Test heating type configuration."""

    def test_default_heating_type(self):
        """Test default heating type is radiator."""
        area = Area("test_area", "Test Area")
        assert area.heating_type == "radiator"
        assert area.custom_overhead_temp is None

    def test_set_floor_heating_type(self):
        """Test setting floor heating type."""
        area = Area("test_area", "Test Area")
        area.heating_type = "floor_heating"
        assert area.heating_type == "floor_heating"

    def test_set_custom_overhead_temp(self):
        """Test setting custom overhead temperature."""
        area = Area("test_area", "Test Area")
        area.custom_overhead_temp = 8.0
        assert area.custom_overhead_temp == 8.0

    def test_heating_type_serialization(self):
        """Test heating type is serialized to dict."""
        area = Area("test_area", "Test Area")
        area.heating_type = "floor_heating"
        area.custom_overhead_temp = 8.0

        data = area.to_dict()
        assert data["heating_type"] == "floor_heating"
        assert data["custom_overhead_temp"] == 8.0

    def test_heating_type_deserialization(self):
        """Test heating type is deserialized from dict."""
        data = {
            "area_id": "test_area",
            "name": "Test Area",
            "target_temperature": 20.0,
            "enabled": True,
            "heating_type": "floor_heating",
            "custom_overhead_temp": 8.0,
        }

        area = Area.from_dict(data)
        assert area.heating_type == "floor_heating"
        assert area.custom_overhead_temp == 8.0

    def test_heating_type_deserialization_defaults(self):
        """Test heating type defaults when not in dict."""
        data = {
            "area_id": "test_area",
            "name": "Test Area",
            "target_temperature": 20.0,
            "enabled": True,
        }

        area = Area.from_dict(data)
        assert area.heating_type == "radiator"
        assert area.custom_overhead_temp is None

    def test_heating_type_backward_compatibility(self):
        """Test backward compatibility with old configs without heating type."""
        data = {
            "area_id": "test_area",
            "name": "Test Area",
            "target_temperature": 20.0,
            "enabled": True,
            "devices": {},
            "schedules": [],
        }

        area = Area.from_dict(data)
        assert area.heating_type == "radiator"
        assert area.custom_overhead_temp is None

    def test_both_radiator_and_floor_heating_types(self):
        """Test both heating types can be set."""
        radiator_area = Area("radiator", "Radiator Room")
        radiator_area.heating_type = "radiator"
        assert radiator_area.heating_type == "radiator"

        floor_area = Area("floor", "Floor Room")
        floor_area.heating_type = "floor_heating"
        assert floor_area.heating_type == "floor_heating"

    def test_custom_overhead_overrides_default(self):
        """Test custom overhead can override default for any type."""
        # Radiator with custom overhead
        radiator_area = Area("radiator", "Radiator Room")
        radiator_area.heating_type = "radiator"
        radiator_area.custom_overhead_temp = 15.0
        assert radiator_area.custom_overhead_temp == 15.0

        # Floor heating with custom overhead
        floor_area = Area("floor", "Floor Room")
        floor_area.heating_type = "floor_heating"
        floor_area.custom_overhead_temp = 5.0
        assert floor_area.custom_overhead_temp == 5.0

    def test_heating_type_persists_across_serialization(self):
        """Test heating type persists through serialization/deserialization cycle."""
        original = Area("test", "Test")
        original.heating_type = "floor_heating"
        original.custom_overhead_temp = 8.0

        # Serialize to dict
        data = original.to_dict()

        # Deserialize from dict
        restored = Area.from_dict(data)

        assert restored.heating_type == "floor_heating"
        assert restored.custom_overhead_temp == 8.0
