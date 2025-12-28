"""Tests for Area manager classes.

These tests verify that the manager classes work correctly and can be integrated
into the Area class to reduce its complexity.
"""

import pytest
from datetime import datetime, timedelta

from smart_heating.models import (
    Area,
    AreaDeviceManager,
    AreaPresetManager,
    AreaScheduleManager,
    AreaSensorManager,
)
from smart_heating.models.schedule import Schedule
from smart_heating.const import (
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
)


class TestAreaDeviceManager:
    """Test AreaDeviceManager."""

    def test_add_device(self):
        """Test adding a device."""
        area = Area("test", "Test Area")
        manager = AreaDeviceManager(area)

        manager.add_device("climate.test", "thermostat")

        assert "climate.test" in area.devices
        assert area.devices["climate.test"]["type"] == "thermostat"

    def test_remove_device(self):
        """Test removing a device."""
        area = Area("test", "Test Area")
        manager = AreaDeviceManager(area)

        manager.add_device("climate.test", "thermostat")
        manager.remove_device("climate.test")

        assert "climate.test" not in area.devices

    def test_get_thermostats(self):
        """Test getting thermostats."""
        area = Area("test", "Test Area")
        manager = AreaDeviceManager(area)

        manager.add_device("climate.test1", "thermostat")
        manager.add_device("sensor.test", "temperature_sensor")
        manager.add_device("climate.test2", "thermostat")

        thermostats = manager.get_thermostats()

        assert len(thermostats) == 2
        assert "climate.test1" in thermostats
        assert "climate.test2" in thermostats
        assert "sensor.test" not in thermostats

    def test_get_temperature_sensors(self):
        """Test getting temperature sensors."""
        area = Area("test", "Test Area")
        manager = AreaDeviceManager(area)

        manager.add_device("sensor.temp1", "temperature_sensor")
        manager.add_device("climate.test", "thermostat")
        manager.add_device("sensor.temp2", "temperature_sensor")

        sensors = manager.get_temperature_sensors()

        assert len(sensors) == 2
        assert "sensor.temp1" in sensors
        assert "sensor.temp2" in sensors
        assert "climate.test" not in sensors

    def test_get_switches(self):
        """Test getting switches."""
        area = Area("test", "Test Area")
        manager = AreaDeviceManager(area)

        manager.add_device("switch.pump1", "switch")
        manager.add_device("climate.test", "thermostat")
        manager.add_device("switch.pump2", "switch")

        switches = manager.get_switches()

        assert len(switches) == 2
        assert "switch.pump1" in switches
        assert "switch.pump2" in switches
        assert "climate.test" not in switches


class TestAreaSensorManager:
    """Test AreaSensorManager."""

    def test_add_window_sensor(self):
        """Test adding a window sensor."""
        area = Area("test", "Test Area")
        manager = AreaSensorManager(area)

        manager.add_window_sensor("binary_sensor.window1", temp_drop=5.0)

        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.window_sensors[0]["temp_drop"] == 5.0
        assert area.window_sensors[0]["action_when_open"] == "reduce_temperature"

    def test_remove_window_sensor(self):
        """Test removing a window sensor."""
        area = Area("test", "Test Area")
        manager = AreaSensorManager(area)

        manager.add_window_sensor("binary_sensor.window1")
        manager.remove_window_sensor("binary_sensor.window1")

        assert len(area.window_sensors) == 0

    def test_add_presence_sensor(self):
        """Test adding a presence sensor."""
        area = Area("test", "Test Area")
        manager = AreaSensorManager(area)

        manager.add_presence_sensor("binary_sensor.motion1")

        assert len(area.presence_sensors) == 1
        assert area.presence_sensors[0]["entity_id"] == "binary_sensor.motion1"

    def test_remove_presence_sensor(self):
        """Test removing a presence sensor."""
        area = Area("test", "Test Area")
        manager = AreaSensorManager(area)

        manager.add_presence_sensor("binary_sensor.motion1")
        manager.remove_presence_sensor("binary_sensor.motion1")

        assert len(area.presence_sensors) == 0


class TestAreaPresetManager:
    """Test AreaPresetManager."""

    def test_set_preset_mode(self):
        """Test setting preset mode."""
        area = Area("test", "Test Area")
        manager = AreaPresetManager(area)

        manager.set_preset_mode(PRESET_AWAY)

        assert area.preset_mode == PRESET_AWAY

    def test_get_preset_temperature_away(self):
        """Test getting away preset temperature."""
        area = Area("test", "Test Area")
        area.away_temp = 15.0
        area.use_global_away = False
        manager = AreaPresetManager(area)

        manager.set_preset_mode(PRESET_AWAY)
        temp = manager.get_preset_temperature()

        assert temp == 15.0

    def test_get_preset_temperature_comfort(self):
        """Test getting comfort preset temperature."""
        area = Area("test", "Test Area")
        area.comfort_temp = 22.0
        area.use_global_comfort = False
        manager = AreaPresetManager(area)

        manager.set_preset_mode(PRESET_COMFORT)
        temp = manager.get_preset_temperature()

        assert temp == 22.0

    def test_set_boost_mode(self):
        """Test setting boost mode."""
        area = Area("test", "Test Area")
        area.target_temperature = 20.0
        manager = AreaPresetManager(area)

        manager.set_boost_mode(duration=30, temp=25.0)

        assert area.boost_manager.boost_mode_active is True
        assert area.boost_manager.boost_duration == 30
        assert area.boost_manager.boost_temp == 25.0
        assert area.boost_manager.boost_end_time is not None

    def test_cancel_boost_mode(self):
        """Test cancelling boost mode."""
        area = Area("test", "Test Area")
        manager = AreaPresetManager(area)

        manager.set_boost_mode(duration=30, temp=25.0)
        manager.cancel_boost_mode()

        assert area.boost_manager.boost_mode_active is False
        assert area.boost_manager.boost_end_time is None

    def test_check_boost_expiry_not_expired(self):
        """Test boost mode expiry check when not expired."""
        area = Area("test", "Test Area")
        manager = AreaPresetManager(area)

        manager.set_boost_mode(duration=30, temp=25.0)
        expired = manager.check_boost_expiry()

        assert expired is False
        assert area.boost_manager.boost_mode_active is True

    def test_check_boost_expiry_expired(self):
        """Test boost mode expiry check when expired."""
        area = Area("test", "Test Area")
        manager = AreaPresetManager(area)

        manager.set_boost_mode(duration=30, temp=25.0)
        # Manually set end time to past
        area.boost_manager.boost_end_time = datetime.now() - timedelta(minutes=1)
        expired = manager.check_boost_expiry()

        assert expired is True
        assert area.boost_manager.boost_mode_active is False


class TestAreaScheduleManager:
    """Test AreaScheduleManager."""

    def test_add_schedule(self):
        """Test adding a schedule."""
        area = Area("test", "Test Area")
        manager = AreaScheduleManager(area)

        schedule = Schedule(
            schedule_id="test_schedule",
            time="08:00",
            temperature=21.0,
            days=[0, 1, 2, 3, 4],  # Weekdays
        )

        manager.add_schedule(schedule)

        assert "test_schedule" in area.schedules
        assert area.schedules["test_schedule"].time == "08:00"
        assert area.schedules["test_schedule"].temperature == 21.0

    def test_remove_schedule(self):
        """Test removing a schedule."""
        area = Area("test", "Test Area")
        manager = AreaScheduleManager(area)

        schedule = Schedule(
            schedule_id="test_schedule",
            time="08:00",
            temperature=21.0,
        )

        manager.add_schedule(schedule)
        manager.remove_schedule("test_schedule")

        assert "test_schedule" not in area.schedules

    def test_is_in_time_period_simple(self):
        """Test time period check for simple period."""
        area = Area("test", "Test Area")
        manager = area.boost_manager

        # Period: 08:00 - 18:00
        # Current time: 10:00
        current_time = datetime.now().replace(hour=10, minute=0)
        result = manager._is_in_time_period(current_time, "08:00", "18:00")

        assert result is True

    def test_is_in_time_period_outside(self):
        """Test time period check outside period."""
        area = Area("test", "Test Area")
        manager = area.boost_manager

        # Period: 08:00 - 18:00
        # Current time: 20:00
        current_time = datetime.now().replace(hour=20, minute=0)
        result = manager._is_in_time_period(current_time, "08:00", "18:00")

        assert result is False

    def test_is_in_time_period_crossing_midnight(self):
        """Test time period check crossing midnight."""
        area = Area("test", "Test Area")
        manager = area.boost_manager

        # Period: 22:00 - 06:00 (crosses midnight)
        # Current time: 02:00
        current_time = datetime.now().replace(hour=2, minute=0)
        result = manager._is_in_time_period(current_time, "22:00", "06:00")

        assert result is True

    def test_apply_night_boost_active(self):
        """Test applying night boost when active."""
        area = Area("test", "Test Area")
        area.boost_manager.night_boost_enabled = True
        area.boost_manager.night_boost_offset = 1.0
        area.boost_manager.night_boost_start_time = "04:00"
        area.boost_manager.night_boost_end_time = "07:00"
        manager = AreaScheduleManager(area)

        # Current time: 05:00 (within boost period)
        current_time = datetime.now().replace(hour=5, minute=0)
        result = manager.apply_night_boost(20.0, current_time)

        assert result == 21.0  # 20.0 + 1.0

    def test_apply_night_boost_inactive(self):
        """Test applying night boost when inactive."""
        area = Area("test", "Test Area")
        area.boost_manager.night_boost_enabled = True
        area.boost_manager.night_boost_offset = 1.0
        area.boost_manager.night_boost_start_time = "04:00"
        area.boost_manager.night_boost_end_time = "07:00"
        manager = AreaScheduleManager(area)

        # Current time: 10:00 (outside boost period)
        current_time = datetime.now().replace(hour=10, minute=0)
        result = manager.apply_night_boost(20.0, current_time)

        assert result == 20.0  # No change

    def test_apply_night_boost_disabled(self):
        """Test applying night boost when disabled."""
        area = Area("test", "Test Area")
        area.boost_manager.night_boost_enabled = False
        manager = AreaScheduleManager(area)

        # Even if in boost period, should not apply
        current_time = datetime.now().replace(hour=5, minute=0)
        result = manager.apply_night_boost(20.0, current_time)

        assert result == 20.0  # No change


class TestManagerIntegration:
    """Test that managers work correctly when used together."""

    def test_managers_coexist(self):
        """Test that multiple managers can work with the same area."""
        area = Area("test", "Test Area")

        # Create all managers
        device_mgr = AreaDeviceManager(area)
        sensor_mgr = AreaSensorManager(area)
        preset_mgr = AreaPresetManager(area)
        schedule_mgr = AreaScheduleManager(area)

        # Use device manager
        device_mgr.add_device("climate.test", "thermostat")

        # Use sensor manager
        sensor_mgr.add_window_sensor("binary_sensor.window1")

        # Use preset manager
        preset_mgr.set_preset_mode(PRESET_AWAY)

        # Use schedule manager
        schedule = Schedule("test", time="08:00", temperature=21.0)
        schedule_mgr.add_schedule(schedule)

        # Verify all changes affected the same area
        assert "climate.test" in area.devices
        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.preset_mode == PRESET_AWAY
        assert "test" in area.schedules
