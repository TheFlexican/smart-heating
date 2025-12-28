"""Test AreaBoostManager."""

import pytest
from datetime import datetime, time, timedelta

from smart_heating.const import PRESET_BOOST, PRESET_NONE
from smart_heating.models.area import Area
from smart_heating.models.area_boost_manager import AreaBoostManager


@pytest.fixture
def sample_area():
    """Create a sample area for testing."""
    return Area(
        area_id="test_area",
        name="Test Area",
        target_temperature=20.0,
    )


@pytest.fixture
def boost_manager(sample_area):
    """Create a boost manager for testing."""
    return AreaBoostManager(sample_area)


class TestAreaBoostManagerInit:
    """Test AreaBoostManager initialization."""

    def test_init_default_values(self, sample_area):
        """Test initialization with default values."""
        manager = AreaBoostManager(sample_area)

        # Regular boost
        assert manager.boost_mode_active is False
        assert manager.boost_duration == 60
        assert manager.boost_temp == 25.0
        assert manager.boost_end_time is None

        # Night boost
        assert manager.night_boost_enabled is False
        assert manager.night_boost_offset == 0.5
        assert manager.night_boost_start_time == "22:00"
        assert manager.night_boost_end_time == "06:00"

        # Smart boost
        assert manager.smart_boost_enabled is False
        assert manager.smart_boost_target_time == "06:00"
        assert manager.weather_entity_id is None
        assert manager.smart_boost_active is False
        assert manager.smart_boost_original_target is None


class TestRegularBoost:
    """Test regular boost mode functionality."""

    def test_activate_boost_default_temp(self, boost_manager, sample_area):
        """Test activating boost with default temperature."""
        boost_manager.activate_boost(60)

        assert boost_manager.boost_mode_active is True
        assert boost_manager.boost_duration == 60
        assert boost_manager.boost_temp == 25.0  # Default
        assert boost_manager.boost_end_time is not None
        assert sample_area.preset_mode == PRESET_BOOST

        # Check that boost_end_time is approximately 60 minutes from now
        expected_end = datetime.now() + timedelta(minutes=60)
        time_diff = abs((boost_manager.boost_end_time - expected_end).total_seconds())
        assert time_diff < 5  # Within 5 seconds

    def test_activate_boost_custom_temp(self, boost_manager, sample_area):
        """Test activating boost with custom temperature."""
        boost_manager.activate_boost(30, temp=22.5)

        assert boost_manager.boost_mode_active is True
        assert boost_manager.boost_duration == 30
        assert boost_manager.boost_temp == 22.5
        assert sample_area.preset_mode == PRESET_BOOST

    def test_cancel_boost(self, boost_manager, sample_area):
        """Test cancelling boost mode."""
        # Activate boost first
        boost_manager.activate_boost(60)
        assert boost_manager.boost_mode_active is True

        # Cancel boost
        boost_manager.cancel_boost()

        assert boost_manager.boost_mode_active is False
        assert boost_manager.boost_end_time is None
        assert sample_area.preset_mode == PRESET_NONE

    def test_cancel_boost_when_not_active(self, boost_manager):
        """Test cancelling boost when not active does nothing."""
        boost_manager.cancel_boost()
        assert boost_manager.boost_mode_active is False

    def test_is_boost_active_true(self, boost_manager):
        """Test is_boost_active when boost is active."""
        boost_manager.activate_boost(60)
        assert boost_manager.is_boost_active() is True

    def test_is_boost_active_false(self, boost_manager):
        """Test is_boost_active when boost is not active."""
        assert boost_manager.is_boost_active() is False

    def test_is_boost_active_expired(self, boost_manager):
        """Test is_boost_active when boost has expired."""
        # Set boost that expired 1 minute ago
        boost_manager.boost_mode_active = True
        boost_manager.boost_end_time = datetime.now() - timedelta(minutes=1)

        assert boost_manager.is_boost_active() is False
        assert boost_manager.boost_mode_active is False  # Should auto-cancel

    def test_check_boost_expiry_not_expired(self, boost_manager):
        """Test check_boost_expiry when boost hasn't expired."""
        boost_manager.activate_boost(60)
        assert boost_manager.check_boost_expiry() is False
        assert boost_manager.boost_mode_active is True

    def test_check_boost_expiry_expired(self, boost_manager):
        """Test check_boost_expiry when boost has expired."""
        # Set boost that expired 1 minute ago
        boost_manager.boost_mode_active = True
        boost_manager.boost_end_time = datetime.now() - timedelta(minutes=1)

        assert boost_manager.check_boost_expiry() is True
        assert boost_manager.boost_mode_active is False

    def test_check_boost_expiry_not_active(self, boost_manager):
        """Test check_boost_expiry when boost is not active."""
        assert boost_manager.check_boost_expiry() is False


class TestNightBoost:
    """Test night boost functionality."""

    def test_is_night_boost_active_disabled(self, boost_manager):
        """Test night boost when disabled."""
        boost_manager.night_boost_enabled = False
        current_time = datetime(2024, 1, 1, 23, 0)  # 11 PM

        assert boost_manager.is_night_boost_active(current_time) is False

    def test_is_night_boost_active_during_period(self, boost_manager):
        """Test night boost during active period."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "06:00"

        # Test at 11 PM
        current_time = datetime(2024, 1, 1, 23, 0)
        assert boost_manager.is_night_boost_active(current_time) is True

        # Test at 2 AM
        current_time = datetime(2024, 1, 1, 2, 0)
        assert boost_manager.is_night_boost_active(current_time) is True

    def test_is_night_boost_active_outside_period(self, boost_manager):
        """Test night boost outside active period."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "06:00"

        # Test at noon
        current_time = datetime(2024, 1, 1, 12, 0)
        assert boost_manager.is_night_boost_active(current_time) is False

    def test_is_night_boost_active_same_start_end(self, boost_manager):
        """Test night boost with same start and end time."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "22:00"

        current_time = datetime(2024, 1, 1, 22, 0)
        assert boost_manager.is_night_boost_active(current_time) is False

    def test_is_night_boost_active_smart_boost_priority(self, boost_manager):
        """Test that smart boost takes priority over night boost."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "06:00"
        boost_manager.smart_boost_active = True

        current_time = datetime(2024, 1, 1, 23, 0)
        assert boost_manager.is_night_boost_active(current_time) is False

    def test_get_night_boost_offset_active(self, boost_manager):
        """Test get_night_boost_offset when active."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_offset = 0.5
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "06:00"

        current_time = datetime(2024, 1, 1, 23, 0)
        assert boost_manager.get_night_boost_offset(current_time) == 0.5

    def test_get_night_boost_offset_inactive(self, boost_manager):
        """Test get_night_boost_offset when inactive."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_offset = 0.5
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "06:00"

        current_time = datetime(2024, 1, 1, 12, 0)  # Noon
        assert boost_manager.get_night_boost_offset(current_time) == 0.0

    def test_apply_night_boost_active(self, boost_manager, sample_area):
        """Test apply_night_boost when active."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_offset = 0.5
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "06:00"

        current_time = datetime(2024, 1, 1, 23, 0)
        target = 20.0

        result = boost_manager.apply_night_boost(target, current_time)
        assert result == 20.5

    def test_apply_night_boost_inactive(self, boost_manager):
        """Test apply_night_boost when inactive."""
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_offset = 0.5
        boost_manager.night_boost_start_time = "22:00"
        boost_manager.night_boost_end_time = "06:00"

        current_time = datetime(2024, 1, 1, 12, 0)  # Noon
        target = 20.0

        result = boost_manager.apply_night_boost(target, current_time)
        assert result == 20.0


class TestTimePeriod:
    """Test time period checking functionality."""

    def test_is_in_time_period_normal(self, boost_manager):
        """Test time period that doesn't cross midnight."""
        current_time = datetime(2024, 1, 1, 10, 0)  # 10:00 AM
        assert boost_manager._is_in_time_period(current_time, "08:00", "18:00") is True
        assert boost_manager._is_in_time_period(current_time, "12:00", "18:00") is False

    def test_is_in_time_period_crosses_midnight(self, boost_manager):
        """Test time period that crosses midnight."""
        # Test at 11 PM (before midnight)
        current_time = datetime(2024, 1, 1, 23, 0)
        assert boost_manager._is_in_time_period(current_time, "22:00", "06:00") is True

        # Test at 2 AM (after midnight)
        current_time = datetime(2024, 1, 1, 2, 0)
        assert boost_manager._is_in_time_period(current_time, "22:00", "06:00") is True

        # Test at noon (outside period)
        current_time = datetime(2024, 1, 1, 12, 0)
        assert boost_manager._is_in_time_period(current_time, "22:00", "06:00") is False

    def test_is_in_time_period_edge_cases(self, boost_manager):
        """Test time period edge cases."""
        # At start time
        current_time = datetime(2024, 1, 1, 22, 0)
        assert boost_manager._is_in_time_period(current_time, "22:00", "06:00") is True

        # At end time (exclusive)
        current_time = datetime(2024, 1, 1, 6, 0)
        assert boost_manager._is_in_time_period(current_time, "22:00", "06:00") is False


class TestSerialization:
    """Test serialization and deserialization."""

    def test_to_dict(self, boost_manager):
        """Test to_dict serialization."""
        boost_manager.boost_mode_active = True
        boost_manager.boost_duration = 30
        boost_manager.boost_temp = 22.0
        boost_manager.boost_end_time = datetime(2024, 1, 1, 12, 30)
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_offset = 0.8
        boost_manager.night_boost_start_time = "23:00"
        boost_manager.night_boost_end_time = "07:00"
        boost_manager.smart_boost_enabled = True
        boost_manager.smart_boost_target_time = "07:00"
        boost_manager.weather_entity_id = "sensor.outdoor_temp"

        data = boost_manager.to_dict()

        assert data["boost_mode_active"] is True
        assert data["boost_duration"] == 30
        assert data["boost_temp"] == 22.0
        assert data["boost_end_time"] == "2024-01-01T12:30:00"
        assert data["night_boost_enabled"] is True
        assert data["night_boost_offset"] == 0.8
        assert data["night_boost_start_time"] == "23:00"
        assert data["night_boost_end_time"] == "07:00"
        assert data["smart_boost_enabled"] is True
        assert data["smart_boost_target_time"] == "07:00"
        assert data["weather_entity_id"] == "sensor.outdoor_temp"

    def test_to_dict_none_values(self, boost_manager):
        """Test to_dict with None values."""
        data = boost_manager.to_dict()

        assert data["boost_mode_active"] is False
        assert data["boost_end_time"] is None
        assert data["weather_entity_id"] is None

    def test_from_dict(self, sample_area):
        """Test from_dict deserialization."""
        data = {
            "boost_mode_active": True,
            "boost_duration": 45,
            "boost_temp": 23.0,
            "boost_end_time": "2024-01-01T13:00:00",
            "night_boost_enabled": True,
            "night_boost_offset": 0.7,
            "night_boost_start_time": "21:00",
            "night_boost_end_time": "05:00",
            "smart_boost_enabled": True,
            "smart_boost_target_time": "05:30",
            "weather_entity_id": "sensor.weather",
        }

        manager = AreaBoostManager.from_dict(data, sample_area)

        assert manager.boost_mode_active is True
        assert manager.boost_duration == 45
        assert manager.boost_temp == 23.0
        assert manager.boost_end_time == datetime(2024, 1, 1, 13, 0)
        assert manager.night_boost_enabled is True
        assert manager.night_boost_offset == 0.7
        assert manager.night_boost_start_time == "21:00"
        assert manager.night_boost_end_time == "05:00"
        assert manager.smart_boost_enabled is True
        assert manager.smart_boost_target_time == "05:30"
        assert manager.weather_entity_id == "sensor.weather"

    def test_from_dict_defaults(self, sample_area):
        """Test from_dict with missing values uses defaults."""
        data = {}
        manager = AreaBoostManager.from_dict(data, sample_area)

        assert manager.boost_mode_active is False
        assert manager.boost_duration == 60
        assert manager.boost_temp == 25.0
        assert manager.boost_end_time is None
        assert manager.night_boost_enabled is False
        assert manager.night_boost_offset == 0.5
        assert manager.night_boost_start_time == "22:00"
        assert manager.night_boost_end_time == "06:00"
        assert manager.smart_boost_enabled is False
        assert manager.smart_boost_target_time == "06:00"
        assert manager.weather_entity_id is None

    def test_round_trip(self, boost_manager, sample_area):
        """Test that to_dict and from_dict round trip correctly."""
        # Set some values
        boost_manager.boost_mode_active = True
        boost_manager.boost_duration = 90
        boost_manager.boost_temp = 24.0
        boost_manager.boost_end_time = datetime(2024, 1, 1, 14, 0)
        boost_manager.night_boost_enabled = True
        boost_manager.night_boost_offset = 1.0

        # Serialize and deserialize
        data = boost_manager.to_dict()
        new_manager = AreaBoostManager.from_dict(data, sample_area)

        # Verify values match
        assert new_manager.boost_mode_active == boost_manager.boost_mode_active
        assert new_manager.boost_duration == boost_manager.boost_duration
        assert new_manager.boost_temp == boost_manager.boost_temp
        assert new_manager.boost_end_time == boost_manager.boost_end_time
        assert new_manager.night_boost_enabled == boost_manager.night_boost_enabled
        assert new_manager.night_boost_offset == boost_manager.night_boost_offset
