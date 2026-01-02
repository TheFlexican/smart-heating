"""Tests for Area model."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest
from smart_heating.models.area import Area
from smart_heating.models.schedule import Schedule

from tests.unit.const import (
    PRESET_COMFORT,
    PRESET_ECO,
    TEST_AREA_ID,
    TEST_AREA_NAME,
    TEST_CURRENT_TEMP,
    TEST_ENTITY_ID,
    TEST_TEMPERATURE,
)


class TestAreaModel:
    """Test Area model."""

    def test_area_init(self):
        """Test Area initialization."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        assert area.area_id == TEST_AREA_ID
        assert area.name == TEST_AREA_NAME
        assert area.target_temperature == TEST_TEMPERATURE
        assert area.current_temperature is None
        assert area.enabled is True
        assert area.preset_mode == "none"
        assert area.hvac_mode == "heat"
        assert area.devices == {}  # Dict, not list
        assert area.window_sensors == []
        assert area.presence_sensors == []

    def test_area_to_dict(self):
        """Test converting Area to dictionary."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        area_dict = area.to_dict()

        assert area_dict["area_id"] == TEST_AREA_ID
        assert area_dict["area_name"] == TEST_AREA_NAME
        assert area_dict["target_temperature"] == TEST_TEMPERATURE
        assert area_dict["enabled"] is True

    def test_from_dict_legacy_switch_shutdown(self):
        """Test that legacy `switch_shutdown_enabled` key is ignored when loading area data."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": TEST_TEMPERATURE,
            "enabled": True,
            "switch_shutdown_enabled": False,
        }

        area = Area.from_dict(data)
        # Legacy key should be ignored; default remains True
        assert area.shutdown_switches_when_idle is True

    def test_area_device_management(self):
        """Test adding and removing devices."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Add device
        area.add_device(TEST_ENTITY_ID, "thermostat")
        assert TEST_ENTITY_ID in area.devices
        assert len(area.devices) == 1
        assert area.devices[TEST_ENTITY_ID]["type"] == "thermostat"

        # Remove device
        area.remove_device(TEST_ENTITY_ID)
        assert TEST_ENTITY_ID not in area.devices
        assert len(area.devices) == 0

    def test_area_get_thermostats(self):
        """Test getting thermostat devices."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        area.add_device("climate.thermostat1", "thermostat")
        area.add_device("climate.thermostat2", "thermostat")
        area.add_device("sensor.temp", "temperature_sensor")

        thermostats = area.get_thermostats()
        assert len(thermostats) == 2
        assert "climate.thermostat1" in thermostats
        assert "climate.thermostat2" in thermostats

        assert "climate.thermostat2" in thermostats

    def test_area_window_sensor_management(self):
        """Test window sensor management."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Add window sensor
        area.add_window_sensor(
            "binary_sensor.window", action_when_open="reduce_temperature", temp_drop=2.0
        )
        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window"
        assert area.window_sensors[0]["action_when_open"] == "reduce_temperature"
        assert area.window_sensors[0]["temp_drop"] == pytest.approx(2.0)

        # Remove window sensor
        area.remove_window_sensor("binary_sensor.window")
        assert len(area.window_sensors) == 0

    def test_area_presence_sensor_management(self):
        """Test presence sensor management."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Add presence sensor
        area.add_presence_sensor("binary_sensor.presence")
        assert len(area.presence_sensors) == 1
        assert area.presence_sensors[0]["entity_id"] == "binary_sensor.presence"

        # Remove presence sensor
        area.remove_presence_sensor("binary_sensor.presence")
        assert len(area.presence_sensors) == 0

    def test_area_schedule_management(self):
        """Test schedule management."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Create a schedule
        schedule = Schedule(
            schedule_id="schedule_1",
            time="07:00",
            temperature=21.0,
            days=[0, 1],
        )

        # Add schedule
        area.add_schedule(schedule)
        assert len(area.schedules) == 1
        assert "schedule_1" in area.schedules

        # Remove schedule
        area.remove_schedule("schedule_1")
        assert len(area.schedules) == 0

    def test_area_boost_mode(self):
        """Test boost mode functionality."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Set boost mode
        area.set_boost_mode(duration=60, temp=25.0)

        assert area.boost_manager.boost_mode_active is True
        assert area.boost_manager.boost_duration == 60
        assert area.boost_manager.boost_temp == pytest.approx(25.0)
        assert area.boost_manager.boost_end_time is not None
        assert area.preset_mode == "boost"

        # Cancel boost mode
        area.cancel_boost_mode()
        assert area.boost_manager.boost_mode_active is False
        assert area.boost_manager.boost_end_time is None
        assert area.preset_mode == "none"

    def test_area_preset_mode_change(self):
        """Test changing preset mode."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        area.set_preset_mode(PRESET_ECO)
        assert area.preset_mode == PRESET_ECO

        area.set_preset_mode(PRESET_COMFORT)
        assert area.preset_mode == PRESET_COMFORT

    def test_area_current_temperature_property(self):
        """Test current temperature property."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Set via property
        area.current_temperature = TEST_CURRENT_TEMP
        assert area.current_temperature == pytest.approx(TEST_CURRENT_TEMP)

        area.current_temperature = 19.5
        assert area.current_temperature == pytest.approx(19.5)

    def test_area_get_preset_temperature(self):
        """Test getting preset temperature."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Set preset mode and check temperature
        area.preset_mode = "eco"
        temp = area.get_preset_temperature()
        assert temp == area.eco_temp

        area.preset_mode = "comfort"
        temp = area.get_preset_temperature()
        assert temp == area.comfort_temp

    def test_area_global_preset_flags(self):
        """Test global preset usage flags."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Default should use global presets
        assert area.use_global_eco is True
        assert area.use_global_comfort is True
        assert area.use_global_home is True

        # Change to custom presets
        area.use_global_eco = False
        assert area.use_global_eco is False


class TestAreaDeviceTypes:
    """Test area device type getter methods."""

    def test_get_temperature_sensors(self):
        """Test getting temperature sensor devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("sensor.temp1", "temperature_sensor")
        area.add_device("sensor.temp2", "temperature_sensor")
        area.add_device("climate.thermostat", "thermostat")

        sensors = area.get_temperature_sensors()

        assert len(sensors) == 2
        assert "sensor.temp1" in sensors
        assert "sensor.temp2" in sensors

    def test_get_opentherm_gateways(self):
        """Test getting OpenTherm gateway devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("climate.otgw1", "opentherm_gateway")
        area.add_device("climate.otgw2", "opentherm_gateway")
        area.add_device("climate.thermostat", "thermostat")

        gateways = area.get_opentherm_gateways()

        assert len(gateways) == 2
        assert "climate.otgw1" in gateways
        assert "climate.otgw2" in gateways

    def test_get_switches(self):
        """Test getting switch devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("switch.pump1", "switch")
        area.add_device("switch.relay1", "switch")
        area.add_device("climate.thermostat", "thermostat")

        switches = area.get_switches()

        assert len(switches) == 2
        assert "switch.pump1" in switches
        assert "switch.relay1" in switches

    def test_get_valves(self):
        """Test getting valve devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("number.valve1", "valve")
        area.add_device("number.valve2", "valve")
        area.add_device("climate.thermostat", "thermostat")

        valves = area.get_valves()

        assert len(valves) == 2
        assert "number.valve1" in valves
        assert "number.valve2" in valves


class TestAreaWindowSensors:
    """Test window sensor functionality."""

    def test_add_window_sensor_with_reduce_temperature(self):
        """Test adding window sensor with reduce_temperature action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 2.5)

        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.window_sensors[0]["action_when_open"] == "reduce_temperature"
        assert area.window_sensors[0]["temp_drop"] == pytest.approx(2.5)

    def test_add_window_sensor_with_turn_off(self):
        """Test adding window sensor with turn_off action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "turn_off")

        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.window_sensors[0]["action_when_open"] == "turn_off"
        assert "temp_drop" not in area.window_sensors[0]

    def test_add_duplicate_window_sensor(self):
        """Test adding duplicate window sensor is prevented."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 2.0)
        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 3.0)  # Duplicate

        # Should still only have one sensor
        assert len(area.window_sensors) == 1

    def test_remove_window_sensor(self):
        """Test removing window sensor."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 2.0)
        area.add_window_sensor("binary_sensor.window2", "turn_off")

        area.remove_window_sensor("binary_sensor.window1")

        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window2"


class TestAreaPresetTemperatures:
    """Test preset temperature handling."""

    def test_get_preset_temperature_with_area_manager(self):
        """Test getting preset temperature with area manager."""

        # Create a mock area manager with global temperatures
        area_manager = Mock()
        area_manager.global_home_temp = 20.0
        area_manager.global_away_temp = 15.0
        area_manager.global_comfort_temp = 22.0
        area_manager.global_eco_temp = 18.0
        area_manager.global_sleep_temp = 17.0
        area_manager.global_activity_temp = 23.0

        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.area_manager = area_manager
        area.use_global_home = True
        area.preset_mode = "home"

        # Should use global temperatures
        temp = area.get_preset_temperature()
        assert temp == pytest.approx(20.0)

    def test_get_preset_temperature_without_area_manager(self):
        """Test getting preset temperature without area manager."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.home_temp = 20.0
        area.preset_mode = "home"
        area.area_manager = None  # No area manager

        # Should use area-specific temperatures
        temp = area.get_preset_temperature()
        assert temp == pytest.approx(20.0)

    def test_get_active_schedule_temperature(self):
        """Test getting temperature from active schedule."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # Add schedule
        schedule = Schedule(
            schedule_id="test_schedule",
            time="08:00",  # Use 'time' instead of 'start_time'
            temperature=21.0,
            days=[0, 1, 2, 3, 4],
        )
        area.schedules["test_schedule"] = schedule

        # Monday at 8:30 AM
        current_time = datetime(2024, 1, 1, 8, 30)  # Monday

        temp = area.get_active_schedule_temperature(current_time)
        assert temp == pytest.approx(21.0)

    def test_get_active_schedule_temperature_no_schedule(self):
        """Test getting temperature when no schedule active."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # No schedules
        current_time = datetime(2024, 1, 1, 8, 30)

        temp = area.get_active_schedule_temperature(current_time)
        assert temp is None

    def test_get_window_open_temperature_turn_off(self):
        """Test getting temperature when window open with turn_off action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        area.add_window_sensor("binary_sensor.window1", "turn_off")
        area.window_is_open = True

        temp = area.sensor_manager.get_window_open_temperature()
        assert temp == pytest.approx(5.0)  # Frost protection

    def test_get_window_open_temperature_reduce(self):
        """Test getting temperature when window open with reduce action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 3.0)
        area.window_is_open = True

        temp = area.sensor_manager.get_window_open_temperature()
        assert temp == pytest.approx(17.0)  # 20.0 - 3.0

    def test_get_window_open_temperature_no_action(self):
        """Test getting temperature when window closed."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 3.0)
        area.window_is_open = False  # Window closed

        temp = area.sensor_manager.get_window_open_temperature()
        assert temp is None


class TestAreaNightBoost:
    """Test night boost functionality."""

    def test_night_boost_with_area_logger(self):
        """Test night boost logging when area logger available."""

        # Create mock hass with data
        hass = Mock()
        hass.data = {"smart_heating": {"area_logger": Mock()}}

        # Create mock area manager
        area_manager = Mock()
        area_manager.hass = hass

        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.area_manager = area_manager
        area.target_temperature = 20.0
        area.boost_manager.night_boost_enabled = True
        area.boost_manager.night_boost_offset = 2.0
        area.boost_manager.night_boost_start_time = "22:00"
        area.boost_manager.night_boost_end_time = "06:00"

        # Test at a time within the boost period
        current_time = datetime(2024, 1, 1, 23, 0)  # 11 PM

        # Should log to area logger
        target = area.schedule_manager.apply_night_boost(20.0, current_time)
        assert target == pytest.approx(22.0)

    def test_night_boost_active_during_period(self):
        """Test night boost applies offset during configured period."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.boost_manager.night_boost_enabled = True
        area.boost_manager.night_boost_offset = 0.5
        area.boost_manager.night_boost_start_time = "03:00"
        area.boost_manager.night_boost_end_time = "07:00"

        # Test during boost period
        current_time = datetime(2024, 1, 1, 5, 30)  # 5:30 AM
        target = area.schedule_manager.apply_night_boost(18.5, current_time)
        assert target == pytest.approx(19.0)  # 18.5 + 0.5

    def test_night_boost_inactive_outside_period(self):
        """Test night boost doesn't apply outside configured period."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.boost_manager.night_boost_enabled = True
        area.boost_manager.night_boost_offset = 0.5
        area.boost_manager.night_boost_start_time = "03:00"
        area.boost_manager.night_boost_end_time = "07:00"

        # Test outside boost period
        current_time = datetime(2024, 1, 1, 10, 0)  # 10 AM
        target = area.schedule_manager.apply_night_boost(18.5, current_time)
        assert target == pytest.approx(18.5)  # No change

    def test_night_boost_works_with_schedule(self):
        """Test night boost works additively on top of active schedule."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.boost_manager.night_boost_enabled = True
        area.boost_manager.night_boost_offset = 0.2
        area.boost_manager.night_boost_start_time = "03:00"
        area.boost_manager.night_boost_end_time = "07:00"
        area.target_temperature = 20.0

        # Add a sleep schedule that overlaps with night boost
        schedule = Schedule(
            schedule_id="sleep1",
            start_time="22:00",
            end_time="06:30",
            day=0,
            preset_mode="sleep",
        )
        area.add_schedule(schedule)
        area.sleep_temp = 18.5

        # Test at 5 AM - during both sleep schedule AND night boost
        current_time = datetime(2024, 1, 1, 5, 0)  # Monday 5 AM

        # Night boost should work on top of sleep temperature
        # Sleep schedule gives 18.5°C, night boost adds 0.2°C = 18.7°C
        target = area.schedule_manager.apply_night_boost(18.5, current_time)
        assert target == pytest.approx(18.7)

    def test_night_boost_disabled(self):
        """Test night boost doesn't apply when disabled."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.boost_manager.night_boost_enabled = False
        area.boost_manager.night_boost_offset = 2.0
        area.boost_manager.night_boost_start_time = "03:00"
        area.boost_manager.night_boost_end_time = "07:00"

        # Test during what would be boost period
        current_time = datetime(2024, 1, 1, 5, 0)
        target = area.schedule_manager.apply_night_boost(20.0, current_time)
        assert target == pytest.approx(20.0)  # No change when disabled

    def test_night_boost_crosses_midnight(self):
        """Test night boost works correctly when period crosses midnight."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.boost_manager.night_boost_enabled = True
        area.boost_manager.night_boost_offset = 0.3
        area.boost_manager.night_boost_start_time = "22:00"
        area.boost_manager.night_boost_end_time = "06:00"

        # Test late night (before midnight)
        current_time = datetime(2024, 1, 1, 23, 30)  # 11:30 PM
        target = area.schedule_manager.apply_night_boost(18.0, current_time)
        assert target == pytest.approx(18.3)

        # Test early morning (after midnight)
        current_time = datetime(2024, 1, 2, 4, 0)  # 4 AM
        target = area.schedule_manager.apply_night_boost(18.0, current_time)
        assert target == pytest.approx(18.3)


class TestAreaState:
    """Test area state property."""

    def test_state_when_disabled(self):
        """Test state returns off when area disabled."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.enabled = False

        assert area.state == "off"

    def test_state_with_explicit_state(self):
        """Test state returns explicit _state when set."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area._state = "heating"

        assert area.state == "heating"

    def test_state_based_on_temperature(self):
        """Test state determined by temperature when no explicit state."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.current_temperature = 18.0
        area.target_temperature = 21.0

        # Should be heating (current < target - 0.5)
        assert area.state == "heating"

    def test_state_idle_when_at_temperature(self):
        """Test state idle when at target temperature."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.current_temperature = 20.0
        area.target_temperature = 20.0

        # Should be idle (current >= target - 0.5)
        assert area.state == "idle"


class TestAreaFromDict:
    """Test Area.from_dict() functionality."""

    def test_from_dict_with_boost_end_time(self):
        """Test loading area with boost_end_time."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "boost_end_time": "2024-01-01T12:00:00",
        }

        area = Area.from_dict(data)

        assert area.boost_manager.boost_end_time is not None
        assert area.boost_manager.boost_end_time.year == 2024

    def test_from_dict_with_hysteresis_override(self):
        """Test loading area with hysteresis_override."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "hysteresis_override": 1.5,
        }

        area = Area.from_dict(data)

        assert area.hysteresis_override == pytest.approx(1.5)

    def test_from_dict_legacy_window_sensors(self):
        """Test loading area with legacy window sensor format."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "window_sensors": ["binary_sensor.window1", "binary_sensor.window2"],
            "window_open_temp_drop": 2.5,
        }

        area = Area.from_dict(data)

        assert len(area.window_sensors) == 2
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.window_sensors[0]["action_when_open"] == "reduce_temperature"
        assert area.window_sensors[0]["temp_drop"] == pytest.approx(2.5)

    def test_from_dict_legacy_presence_sensors(self):
        """Test loading area with legacy presence sensor format."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "presence_sensors": ["binary_sensor.motion1", "binary_sensor.motion2"],
            "presence_temp_boost": 1.5,
        }

        area = Area.from_dict(data)

        assert len(area.presence_sensors) == 2
        assert area.presence_sensors[0]["entity_id"] == "binary_sensor.motion1"
        assert area.presence_sensors[0]["temp_boost_when_home"] == pytest.approx(1.5)

    def test_from_dict_with_auto_preset(self):
        """Test loading area with auto preset settings."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "auto_preset_enabled": True,
            "auto_preset_home": "comfort",
            "auto_preset_away": "eco",
        }

        area = Area.from_dict(data)

        assert area.auto_preset_enabled is True
        assert area.auto_preset_home == "comfort"
        assert area.auto_preset_away == "eco"


class TestAreaTRVEntities:
    """Test TRV entity management."""

    def test_add_trv_entity(self):
        """Test adding TRV entity."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_trv_entity("sensor.trv_position", role="position", name="Living Room TRV")

        assert len(area.trv_entities) == 1
        assert area.trv_entities[0]["entity_id"] == "sensor.trv_position"
        assert area.trv_entities[0]["role"] == "position"
        assert area.trv_entities[0]["name"] == "Living Room TRV"

    def test_add_trv_entity_without_role(self):
        """Test adding TRV entity without role."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_trv_entity("sensor.trv_position")

        assert len(area.trv_entities) == 1
        assert area.trv_entities[0]["entity_id"] == "sensor.trv_position"
        assert area.trv_entities[0]["role"] is None
        assert area.trv_entities[0]["name"] is None

    def test_add_duplicate_trv_entity_updates(self):
        """Test adding duplicate TRV entity updates existing entry."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_trv_entity("sensor.trv_position", role="position", name="Name 1")
        area.add_trv_entity("sensor.trv_position", role="both", name="Name 2")

        # Should only have one entity, with updated values
        assert len(area.trv_entities) == 1
        assert area.trv_entities[0]["role"] == "both"
        assert area.trv_entities[0]["name"] == "Name 2"

    def test_remove_trv_entity(self):
        """Test removing TRV entity."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_trv_entity("sensor.trv_position1", role="position")
        area.add_trv_entity("sensor.trv_position2", role="open")

        area.remove_trv_entity("sensor.trv_position1")

        assert len(area.trv_entities) == 1
        assert area.trv_entities[0]["entity_id"] == "sensor.trv_position2"

    def test_remove_nonexistent_trv_entity(self):
        """Test removing TRV entity that doesn't exist."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_trv_entity("sensor.trv_position", role="position")
        area.remove_trv_entity("sensor.nonexistent")

        # Original entity should still be there
        assert len(area.trv_entities) == 1


class TestAreaBoostExpiry:
    """Test boost mode expiry checking."""

    def test_check_boost_expiry_when_expired(self):
        """Test boost mode is cancelled when expired."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # Set boost mode to expire in the past
        past_time = datetime(2024, 1, 1, 10, 0, 0)
        area.boost_manager.boost_mode_active = True
        area.boost_manager.boost_end_time = past_time
        area.preset_mode = "boost"

        # Check expiry (current time is after boost end time)
        expired = area.check_boost_expiry()

        assert expired is True
        assert area.boost_manager.boost_mode_active is False
        assert area.boost_manager.boost_end_time is None
        assert area.preset_mode == "none"

    def test_check_boost_expiry_when_active(self):
        """Test boost mode is not cancelled when still active."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # Set boost mode to expire in the future
        from datetime import timedelta

        future_time = datetime.now() + timedelta(minutes=30)
        area.boost_manager.boost_mode_active = True
        area.boost_manager.boost_end_time = future_time
        area.preset_mode = "boost"

        # Check expiry
        expired = area.check_boost_expiry()

        assert expired is False
        assert area.boost_manager.boost_mode_active is True

    def test_check_boost_expiry_when_not_active(self):
        """Test boost expiry check when boost not active."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.boost_manager.boost_mode_active = False

        expired = area.check_boost_expiry()

        assert expired is False


class TestAreaEffectiveTargetTemperature:
    """Test get_effective_target_temperature logic."""

    def test_effective_temperature_with_boost(self):
        """Test boost mode takes priority."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0
        area.preset_mode = "boost"
        area.boost_manager.boost_mode_active = True
        area.boost_manager.boost_temp = 25.0

        temp = area.get_effective_target_temperature()

        assert temp == pytest.approx(25.0)

    def test_effective_temperature_with_window_open(self):
        """Test window open reduces temperature."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0
        area.add_window_sensor("binary_sensor.window", "reduce_temperature", 3.0)
        area.window_is_open = True

        temp = area.get_effective_target_temperature()

        # Should reduce by 3 degrees
        assert temp == pytest.approx(17.0)

    def test_effective_temperature_with_preset(self):
        """Test preset mode temperature."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0
        area.preset_mode = "eco"
        area.eco_temp = 18.0

        temp = area.get_effective_target_temperature()

        assert temp == pytest.approx(18.0)

    def test_effective_temperature_with_schedule(self):
        """Test schedule temperature."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        # Add a schedule for Monday morning
        schedule = Schedule(
            schedule_id="morning",
            time="08:00",
            temperature=21.5,
            days=[0],  # Monday
        )
        area.add_schedule(schedule)

        # Test at Monday 8:30 AM
        current_time = datetime(2024, 1, 1, 8, 30)  # Monday

        temp = area.get_effective_target_temperature(current_time)

        assert temp == pytest.approx(21.5)

    def test_effective_temperature_base_target(self):
        """Test base target temperature when no overrides."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        temp = area.get_effective_target_temperature()

        assert temp == pytest.approx(20.0)

    def test_effective_temperature_priority_boost_over_window(self):
        """Test boost mode takes priority over window open."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0
        area.boost_manager.boost_mode_active = True
        area.boost_manager.boost_temp = 25.0
        area.preset_mode = "boost"
        area.add_window_sensor("binary_sensor.window", "reduce_temperature", 3.0)
        area.window_is_open = True

        temp = area.get_effective_target_temperature()

        # Boost should take priority
        assert temp == pytest.approx(25.0)

    def test_effective_temperature_priority_window_over_preset(self):
        """Test window open takes priority over preset."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0
        area.preset_mode = "comfort"
        area.comfort_temp = 22.0
        area.add_window_sensor("binary_sensor.window", "reduce_temperature", 3.0)
        area.window_is_open = True

        temp = area.get_effective_target_temperature()

        # Window reduces from base target_temperature (20.0), not preset temp
        # This tests the actual priority in the implementation
        assert temp == pytest.approx(17.0)  # 20.0 - 3.0


class TestAreaStateSetter:
    """Test area state setter."""

    def test_state_setter(self):
        """Test setting state explicitly."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.state = "heating"
        assert area.state == "heating"

        area.state = "idle"
        assert area.state == "idle"

    def test_state_setter_overrides_temperature_based(self):
        """Test explicit state takes priority over temperature-based state."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.current_temperature = 18.0
        area.target_temperature = 21.0

        # Set explicit state
        area.state = "idle"

        # Should return explicit state, not temperature-based
        assert area.state == "idle"


class TestAreaSerializationEdgeCases:
    """Test edge cases in serialization."""

    def test_to_dict_includes_all_fields(self):
        """Test to_dict includes all expected fields."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.heating_type = "floor_heating"
        area.custom_overhead_temp = 5.0
        area.heating_curve_coefficient = 1.5
        area.primary_temperature_sensor = "sensor.primary"

        data = area.to_dict()

        # Check heating type fields
        assert "heating_type" in data
        assert data["heating_type"] == "floor_heating"
        assert "custom_overhead_temp" in data
        assert data["custom_overhead_temp"] == pytest.approx(5.0)

        # Check sensor field
        assert "primary_temperature_sensor" in data
        assert data["primary_temperature_sensor"] == "sensor.primary"

        # Check TRV entities
        assert "trv_entities" in data
        assert data["trv_entities"] == []

    def test_to_dict_with_schedules(self):
        """Test to_dict includes schedules."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        schedule = Schedule(
            schedule_id="test",
            time="08:00",
            temperature=21.0,
            days=[0, 1],
        )
        area.add_schedule(schedule)

        data = area.to_dict()

        assert "schedules" in data
        assert len(data["schedules"]) == 1
        # Schedule.to_dict() uses "id" not "schedule_id"
        assert data["schedules"][0]["id"] == "test"

    def test_from_dict_with_heating_type(self):
        """Test from_dict loads heating type correctly."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "heating_type": "airco",
            "custom_overhead_temp": 10.0,
        }

        area = Area.from_dict(data)

        assert area.heating_type == "airco"
        assert area.custom_overhead_temp == pytest.approx(10.0)

    def test_from_dict_with_trv_entities(self):
        """Test from_dict loads TRV entities."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "trv_entities": [
                {"entity_id": "sensor.trv1", "role": "position", "name": "TRV 1"},
                {"entity_id": "sensor.trv2", "role": "open", "name": "TRV 2"},
            ],
        }

        area = Area.from_dict(data)

        assert len(area.trv_entities) == 2
        assert area.trv_entities[0]["entity_id"] == "sensor.trv1"
        assert area.trv_entities[1]["role"] == "open"

    def test_from_dict_defaults_heating_type(self):
        """Test from_dict defaults heating type to radiator."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
        }

        area = Area.from_dict(data)

        assert area.heating_type == "radiator"
        assert area.custom_overhead_temp is None


class TestAreaDeviceManagementEdgeCases:
    """Test edge cases in device management."""

    def test_add_device_with_mqtt_topic(self):
        """Test adding device with MQTT topic."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("climate.thermostat", "thermostat", "home/thermostat/control")

        assert "climate.thermostat" in area.devices
        assert area.devices["climate.thermostat"]["mqtt_topic"] == "home/thermostat/control"

    def test_add_device_without_mqtt_topic(self):
        """Test adding device without MQTT topic."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("climate.thermostat", "thermostat")

        assert "climate.thermostat" in area.devices
        # mqtt_topic should not be in dict or be None
        mqtt_topic = area.devices["climate.thermostat"].get("mqtt_topic")
        assert mqtt_topic is None or mqtt_topic == ""

    def test_remove_device_that_doesnt_exist(self):
        """Test removing device that doesn't exist doesn't raise error."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # Should not raise
        area.remove_device("climate.nonexistent")
        assert len(area.devices) == 0

    def test_boost_mode_with_default_temp(self):
        """Test setting boost mode without specifying temperature."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.boost_manager.boost_temp = 24.0

        # Set boost without temp parameter - should use area.boost_manager.boost_temp
        area.set_boost_mode(duration=30)

        assert area.boost_manager.boost_mode_active is True
        assert area.boost_manager.boost_temp == pytest.approx(24.0)


class TestAreaInitializationDefaults:
    """Test default values during initialization."""

    def test_area_default_values(self):
        """Test all default values are set correctly."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # Night boost defaults
        assert area.boost_manager.night_boost_enabled is False
        assert area.boost_manager.night_boost_offset == pytest.approx(0.5)

        # Smart boost defaults
        assert area.boost_manager.smart_boost_enabled is False
        assert area.boost_manager.smart_boost_target_time == "06:00"
        assert area.boost_manager.smart_boost_active is False
        assert area.boost_manager.smart_boost_original_target is None

        # Boost defaults
        assert area.boost_manager.boost_mode_active is False
        assert area.boost_manager.boost_duration == 60
        assert area.boost_manager.boost_temp == pytest.approx(25.0)

        # HVAC mode
        assert area.hvac_mode == "heat"

        # Auto preset defaults
        assert area.auto_preset_enabled is False

        # Hysteresis override
        assert area.hysteresis_override is None

        # Heating type
        assert area.heating_type == "radiator"
        assert area.custom_overhead_temp is None
        assert area.heating_curve_coefficient is None

        # State tracking
        assert area._last_heating_state is None

        # Manual override
        assert area.manual_override is False

        # Shutdown switches
        assert area.shutdown_switches_when_idle is True

    def test_area_managers_initialized(self):
        """Test manager instances are created."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        assert area.device_manager is not None
        assert area.sensor_manager is not None
        assert area.preset_manager is not None
        assert area.schedule_manager is not None


class TestAreaSmartBoost:
    """Test smart boost attributes."""

    def test_smart_boost_attributes(self):
        """Test smart boost attributes can be set."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.boost_manager.smart_boost_enabled = True
        area.boost_manager.smart_boost_target_time = "07:30"
        area.boost_manager.weather_entity_id = "weather.home"
        area.boost_manager.smart_boost_active = True
        area.boost_manager.smart_boost_original_target = 20.0

        assert area.boost_manager.smart_boost_enabled is True
        assert area.boost_manager.smart_boost_target_time == "07:30"
        assert area.boost_manager.weather_entity_id == "weather.home"
        assert area.boost_manager.smart_boost_active is True
        assert area.boost_manager.smart_boost_original_target == pytest.approx(20.0)

    def test_smart_boost_in_serialization(self):
        """Test smart boost fields in serialization."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.boost_manager.smart_boost_enabled = True
        area.boost_manager.smart_boost_target_time = "07:00"
        area.boost_manager.weather_entity_id = "weather.forecast"

        data = area.to_dict()

        assert data["smart_boost_enabled"] is True
        assert data["smart_boost_target_time"] == "07:00"
        assert data["weather_entity_id"] == "weather.forecast"

    def test_smart_boost_from_dict(self):
        """Test loading smart boost from dict."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "smart_boost_enabled": True,
            "smart_boost_target_time": "07:30",
            "weather_entity_id": "weather.home",
        }

        area = Area.from_dict(data)

        assert area.boost_manager.smart_boost_enabled is True
        assert area.boost_manager.smart_boost_target_time == "07:30"
        assert area.boost_manager.weather_entity_id == "weather.home"


class TestAreaHiddenAndManualOverride:
    """Test hidden and manual override flags."""

    def test_hidden_flag(self):
        """Test area hidden flag."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        assert area.hidden is False

        area.hidden = True
        assert area.hidden is True

    def test_manual_override_flag(self):
        """Test manual override flag."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        assert area.manual_override is False

        area.manual_override = True
        assert area.manual_override is True

    def test_hidden_in_serialization(self):
        """Test hidden flag in serialization."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.hidden = True

        data = area.to_dict()

        assert data["hidden"] is True

        # Test round-trip
        area2 = Area.from_dict(data)
        assert area2.hidden is True


class TestAreaPIDPersistence:
    """Test PID settings persistence in Area model."""

    def test_area_default_pid_settings(self):
        """Test area initializes with default PID settings."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        assert area.pid_enabled is False
        assert area.pid_automatic_gains is True
        assert area.pid_active_modes == ["schedule", "home", "comfort"]

    def test_pid_settings_in_to_dict(self):
        """Test PID settings are included in to_dict."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        area.pid_enabled = True
        area.pid_automatic_gains = False
        area.pid_active_modes = ["home", "away"]

        data = area.to_dict()

        assert data["pid_enabled"] is True
        assert data["pid_automatic_gains"] is False
        assert data["pid_active_modes"] == ["home", "away"]

    def test_pid_settings_from_dict(self):
        """Test loading PID settings from dict."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": TEST_TEMPERATURE,
            "pid_enabled": True,
            "pid_automatic_gains": False,
            "pid_active_modes": ["schedule", "comfort", "eco"],
        }

        area = Area.from_dict(data)

        assert area.pid_enabled is True
        assert area.pid_automatic_gains is False
        assert area.pid_active_modes == ["schedule", "comfort", "eco"]

    def test_pid_settings_defaults_when_missing(self):
        """Test PID settings use defaults when not in dict."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": TEST_TEMPERATURE,
        }

        area = Area.from_dict(data)

        # Should use defaults
        assert area.pid_enabled is False
        assert area.pid_automatic_gains is True
        assert area.pid_active_modes == ["schedule", "home", "comfort"]

    def test_pid_settings_roundtrip(self):
        """Test PID settings survive to_dict -> from_dict roundtrip."""
        area1 = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        area1.pid_enabled = True
        area1.pid_automatic_gains = False
        area1.pid_active_modes = ["home", "schedule"]

        data = area1.to_dict()
        area2 = Area.from_dict(data)

        assert area2.pid_enabled == area1.pid_enabled
        assert area2.pid_automatic_gains == area1.pid_automatic_gains
        assert area2.pid_active_modes == area1.pid_active_modes

    def test_heating_curve_coefficient_persists(self):
        """Test heating_curve_coefficient is persisted (bug fix verification)."""
        area1 = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        area1.heating_curve_coefficient = 2.5

        data = area1.to_dict()
        assert "heating_curve_coefficient" in data
        assert data["heating_curve_coefficient"] == 2.5

        area2 = Area.from_dict(data)
        assert area2.heating_curve_coefficient == 2.5

    def test_heating_curve_coefficient_none_persists(self):
        """Test heating_curve_coefficient None is persisted."""
        area1 = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        area1.heating_curve_coefficient = None

        data = area1.to_dict()
        area2 = Area.from_dict(data)
        assert area2.heating_curve_coefficient is None

    def test_pid_active_modes_empty_list(self):
        """Test PID active modes can be empty list."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        area.pid_active_modes = []

        data = area.to_dict()
        area2 = Area.from_dict(data)

        assert area2.pid_active_modes == []

    def test_pid_active_modes_all_valid_modes(self):
        """Test PID active modes with all valid modes."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        all_modes = ["schedule", "home", "away", "sleep", "comfort", "eco", "boost", "manual"]
        area.pid_active_modes = all_modes

        data = area.to_dict()
        area2 = Area.from_dict(data)

        assert area2.pid_active_modes == all_modes


class TestAreaFromDictCompatibility:
    """Test from_dict compatibility with different data formats."""

    def test_from_dict_with_name_instead_of_area_name(self):
        """Test from_dict accepts 'name' field for compatibility."""
        data = {
            "area_id": TEST_AREA_ID,
            "name": "Test Name",  # Using 'name' instead of 'area_name'
            "target_temperature": 20.0,
        }

        area = Area.from_dict(data)

        assert area.name == "Test Name"

    def test_from_dict_minimal_data(self):
        """Test from_dict with minimal required data."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
        }

        area = Area.from_dict(data)

        assert area.area_id == TEST_AREA_ID
        assert area.name == TEST_AREA_NAME
        assert area.target_temperature == pytest.approx(20.0)  # Default
        assert area.enabled is True  # Default

    def test_from_dict_with_all_preset_modes(self):
        """Test from_dict loads all preset mode temperatures."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "away_temp": 15.0,
            "eco_temp": 17.0,
            "comfort_temp": 22.0,
            "home_temp": 20.0,
            "sleep_temp": 18.0,
            "activity_temp": 23.0,
        }

        area = Area.from_dict(data)

        assert area.away_temp == pytest.approx(15.0)
        assert area.eco_temp == pytest.approx(17.0)
        assert area.comfort_temp == pytest.approx(22.0)
        assert area.home_temp == pytest.approx(20.0)
        assert area.sleep_temp == pytest.approx(18.0)
        assert area.activity_temp == pytest.approx(23.0)
