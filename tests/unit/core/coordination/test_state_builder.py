"""Test StateBuilder component."""

import pytest
from unittest.mock import MagicMock, Mock

from smart_heating.core.coordination.state_builder import StateBuilder
from smart_heating.models import Area


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_coordinator(mock_hass):
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.hass = mock_hass
    coordinator._get_device_state_data = MagicMock(
        return_value={
            "id": "climate.test",
            "type": "thermostat",
            "state": "heat",
            "name": "Test Thermostat",
        }
    )
    coordinator._get_weather_state_data = MagicMock(return_value=None)
    coordinator._get_trv_states_for_area = MagicMock(return_value=[])
    return coordinator


@pytest.fixture
def sample_area():
    """Create a sample Area instance."""
    area = Area(
        area_id="living_room",
        name="Living Room",
        target_temperature=20.0,
        enabled=True,
    )
    area.current_temperature = 19.5
    area.state = "heating"
    area.preset_mode = "comfort"
    area.hvac_mode = "heat"
    area.devices = {
        "climate.thermostat": {"type": "thermostat"},
    }
    area.window_sensors = []
    area.presence_sensors = []
    area.manual_override = False
    area.hidden = False
    area.boost_manager.boost_mode_active = False
    area.boost_manager.boost_temp = 24.0
    area.boost_manager.boost_duration = 60
    area.hysteresis_override = None
    area.shutdown_switches_when_idle = True
    area.boost_manager.night_boost_enabled = False
    area.boost_manager.night_boost_offset = 0.5
    area.boost_manager.night_boost_start_time = "22:00"
    area.boost_manager.night_boost_end_time = "06:00"
    area.boost_manager.smart_boost_enabled = False
    area.boost_manager.smart_boost_target_time = "06:00"
    area.boost_manager.weather_entity_id = None
    area.primary_temperature_sensor = None
    area.heating_type = "radiator"
    area.custom_overhead_temp = None
    area.heating_curve_coefficient = None
    area.trv_entities = []
    return area


class TestStateBuilder:
    """Test StateBuilder functionality."""

    def test_build_basic_info(self, mock_hass, mock_coordinator, sample_area):
        """Test building basic area info."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        info = builder._build_basic_info("living_room", sample_area)

        assert info["id"] == "living_room"
        assert info["name"] == "Living Room"
        assert info["enabled"] is True
        assert info["state"] == "heating"
        assert info["device_count"] == 1
        assert info["hidden"] is False
        assert info["manual_override"] is False

    def test_build_temperature_data(self, mock_hass, mock_coordinator, sample_area):
        """Test building temperature data."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.current_temperature = 19.5
        sample_area.target_temperature = 20.0

        temp_data = builder._build_temperature_data(sample_area)

        assert temp_data["current_temperature"] == 19.5
        assert temp_data["target_temperature"] == 20.0
        assert "effective_target_temperature" in temp_data

    def test_build_device_states(self, mock_hass, mock_coordinator, sample_area):
        """Test building device states."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.devices = {"climate.thermostat": {"type": "thermostat"}}

        device_data = builder._build_device_states(sample_area)

        assert "devices" in device_data
        assert len(device_data["devices"]) == 1
        mock_coordinator._get_device_state_data.assert_called_once()

    def test_build_schedule_info(self, mock_hass, mock_coordinator, sample_area):
        """Test building schedule information."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        # Add a mock schedule
        mock_schedule = MagicMock()
        mock_schedule.to_dict = MagicMock(
            return_value={
                "id": "schedule_1",
                "time": "07:00",
                "temperature": 21.0,
                "enabled": True,
            }
        )
        sample_area.schedules = {"schedule_1": mock_schedule}

        schedule_data = builder._build_schedule_info(sample_area)

        assert "schedules" in schedule_data
        assert len(schedule_data["schedules"]) == 1
        assert schedule_data["schedules"][0]["id"] == "schedule_1"

    def test_build_preset_settings(self, mock_hass, mock_coordinator, sample_area):
        """Test building preset settings."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        preset_data = builder._build_preset_settings(sample_area)

        assert preset_data["preset_mode"] == "comfort"
        assert "away_temp" in preset_data
        assert "eco_temp" in preset_data
        assert "comfort_temp" in preset_data
        assert "home_temp" in preset_data
        assert "sleep_temp" in preset_data
        assert "activity_temp" in preset_data
        assert "use_global_away" in preset_data
        assert "auto_preset_enabled" in preset_data

    def test_build_boost_mode(self, mock_hass, mock_coordinator, sample_area):
        """Test building boost mode settings."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.boost_manager.boost_mode_active = True
        sample_area.boost_manager.boost_temp = 24.0
        sample_area.boost_manager.boost_duration = 120

        boost_data = builder._build_boost_mode(sample_area)

        assert boost_data["boost_mode_active"] is True
        assert boost_data["boost_temp"] == 24.0
        assert boost_data["boost_duration"] == 120

    def test_build_sensor_config(self, mock_hass, mock_coordinator, sample_area):
        """Test building sensor configuration."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.window_sensors = ["binary_sensor.window"]
        sample_area.presence_sensors = ["binary_sensor.motion"]
        sample_area.primary_temperature_sensor = "sensor.temp"

        sensor_data = builder._build_sensor_config(sample_area)

        assert sensor_data["window_sensors"] == ["binary_sensor.window"]
        assert sensor_data["presence_sensors"] == ["binary_sensor.motion"]
        assert sensor_data["primary_temperature_sensor"] == "sensor.temp"

    def test_build_night_boost_config(self, mock_hass, mock_coordinator, sample_area):
        """Test building night boost configuration."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.boost_manager.night_boost_enabled = True
        sample_area.boost_manager.night_boost_offset = 1.0
        sample_area.boost_manager.night_boost_start_time = "22:00"
        sample_area.boost_manager.night_boost_end_time = "06:00"

        night_boost_data = builder._build_night_boost_config(sample_area)

        assert night_boost_data["night_boost_enabled"] is True
        assert night_boost_data["night_boost_offset"] == 1.0
        assert night_boost_data["night_boost_start_time"] == "22:00"
        assert night_boost_data["night_boost_end_time"] == "06:00"

    def test_build_smart_boost_config(self, mock_hass, mock_coordinator, sample_area):
        """Test building smart boost configuration."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.boost_manager.smart_boost_enabled = True
        sample_area.boost_manager.smart_boost_target_time = "07:00"
        sample_area.boost_manager.weather_entity_id = "weather.home"

        mock_coordinator._get_weather_state_data.return_value = {
            "entity_id": "weather.home",
            "temperature": 5.0,
        }

        smart_boost_data = builder._build_smart_boost_config(sample_area)

        assert smart_boost_data["smart_boost_enabled"] is True
        assert smart_boost_data["smart_boost_target_time"] == "07:00"
        assert smart_boost_data["weather_entity_id"] == "weather.home"
        assert smart_boost_data["weather_state"]["temperature"] == 5.0

    def test_build_control_state(self, mock_hass, mock_coordinator, sample_area):
        """Test building control state information."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.hvac_mode = "heat"
        sample_area.hysteresis_override = 0.5
        sample_area.shutdown_switches_when_idle = False

        control_data = builder._build_control_state(sample_area)

        assert control_data["hvac_mode"] == "heat"
        assert control_data["hysteresis_override"] == 0.5
        assert control_data["shutdown_switches_when_idle"] is False

    def test_build_heating_config(self, mock_hass, mock_coordinator, sample_area):
        """Test building heating configuration."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.heating_type = "underfloor"
        sample_area.custom_overhead_temp = 25.0
        sample_area.heating_curve_coefficient = 1.5

        heating_data = builder._build_heating_config(sample_area)

        assert heating_data["heating_type"] == "underfloor"
        assert heating_data["custom_overhead_temp"] == 25.0
        assert heating_data["heating_curve_coefficient"] == 1.5

    def test_build_trv_states(self, mock_hass, mock_coordinator, sample_area):
        """Test building TRV states."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.trv_entities = [
            {"entity_id": "climate.trv1"},
            {"entity_id": "climate.trv2"},
        ]

        mock_coordinator._get_trv_states_for_area.return_value = [
            {"entity_id": "climate.trv1", "open": True, "position": 80, "running_state": "heating"},
            {"entity_id": "climate.trv2", "open": True, "position": 60, "running_state": "heating"},
        ]

        trv_data = builder._build_trv_states(sample_area)

        assert len(trv_data["trv_entities"]) == 2
        assert len(trv_data["trvs"]) == 2
        assert trv_data["trvs"][0]["position"] == 80

    def test_build_area_data_complete(self, mock_hass, mock_coordinator, sample_area):
        """Test building complete area data."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        area_data = builder.build_area_data("living_room", sample_area)

        # Verify all sections present
        assert "id" in area_data
        assert "name" in area_data
        assert "enabled" in area_data
        assert "state" in area_data
        assert "target_temperature" in area_data
        assert "current_temperature" in area_data
        assert "effective_target_temperature" in area_data
        assert "devices" in area_data
        assert "schedules" in area_data
        assert "preset_mode" in area_data
        assert "boost_mode_active" in area_data
        assert "window_sensors" in area_data
        assert "night_boost_enabled" in area_data
        assert "smart_boost_enabled" in area_data
        assert "hvac_mode" in area_data
        assert "heating_type" in area_data
        assert "trv_entities" in area_data

    def test_build_area_data_with_defaults(self, mock_hass, mock_coordinator):
        """Test building area data with default values."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        # Create area with minimal data
        area = Area(
            area_id="minimal",
            name="Minimal Area",
        )

        area_data = builder.build_area_data("minimal", area)

        # Should have all keys with sensible defaults
        assert area_data["id"] == "minimal"
        assert area_data["name"] == "Minimal Area"
        assert area_data["enabled"] is True
        assert area_data["manual_override"] is False
        assert area_data["hidden"] is False

    def test_build_area_data_hidden_area(self, mock_hass, mock_coordinator, sample_area):
        """Test building data for hidden area."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.hidden = True

        area_data = builder.build_area_data("living_room", sample_area)

        assert area_data["hidden"] is True

    def test_build_area_data_manual_override(self, mock_hass, mock_coordinator, sample_area):
        """Test building data with manual override active."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.manual_override = True
        sample_area.target_temperature = 22.0

        area_data = builder.build_area_data("living_room", sample_area)

        assert area_data["manual_override"] is True
        assert area_data["target_temperature"] == 22.0

    def test_build_area_data_with_weather(self, mock_hass, mock_coordinator, sample_area):
        """Test building data with weather information."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.boost_manager.weather_entity_id = "weather.home"
        mock_coordinator._get_weather_state_data.return_value = {
            "entity_id": "weather.home",
            "temperature": 5.0,
            "attributes": {"humidity": 80},
        }

        area_data = builder.build_area_data("living_room", sample_area)

        assert area_data["weather_entity_id"] == "weather.home"
        assert area_data["weather_state"]["temperature"] == 5.0

    def test_build_preset_settings_with_global_flags(
        self, mock_hass, mock_coordinator, sample_area
    ):
        """Test building preset settings with global flags."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.use_global_away = True
        sample_area.use_global_eco = False
        sample_area.use_global_comfort = True

        preset_data = builder._build_preset_settings(sample_area)

        assert preset_data["use_global_away"] is True
        assert preset_data["use_global_eco"] is False
        assert preset_data["use_global_comfort"] is True

    def test_build_area_data_auto_preset_enabled(self, mock_hass, mock_coordinator, sample_area):
        """Test building data with auto preset enabled."""
        builder = StateBuilder(mock_hass, mock_coordinator)

        sample_area.auto_preset_enabled = True
        sample_area.auto_preset_home = "comfort"
        sample_area.auto_preset_away = "eco"

        area_data = builder.build_area_data("living_room", sample_area)

        assert area_data["auto_preset_enabled"] is True
        assert area_data["auto_preset_home"] == "comfort"
        assert area_data["auto_preset_away"] == "eco"
