"""Tests for Area Manager."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from smart_heating.const import (
    DEFAULT_AWAY_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_ECO_TEMP,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from smart_heating.core.area_manager import AreaManager
from smart_heating.models import Area

from tests.unit.const import TEST_AREA_ID, TEST_AREA_NAME


@pytest.fixture
def area_manager(hass: HomeAssistant) -> AreaManager:
    """Create an AreaManager instance."""
    return AreaManager(hass)


class TestAreaManagerInitialization:
    """Test AreaManager initialization."""

    def test_init(self, area_manager: AreaManager, hass: HomeAssistant):
        """Test AreaManager initialization."""
        assert area_manager.hass == hass
        assert area_manager.areas == {}
        assert isinstance(area_manager._persistence_service._store, Store)
        assert area_manager.opentherm_gateway_id is None
        assert area_manager.global_eco_temp == DEFAULT_ECO_TEMP
        assert area_manager.global_comfort_temp == DEFAULT_COMFORT_TEMP
        assert area_manager.global_away_temp == DEFAULT_AWAY_TEMP

    def test_storage_configuration(self, area_manager: AreaManager):
        """Test storage configuration."""
        assert area_manager._persistence_service._store.version == STORAGE_VERSION
        assert area_manager._persistence_service._store.key == STORAGE_KEY


class TestAreaManagerLoading:
    """Test AreaManager loading from storage."""

    async def test_async_load_empty_storage(self, area_manager: AreaManager):
        """Test loading with empty storage."""
        with patch.object(
            area_manager._persistence_service._store, "async_load", return_value=None
        ):
            await area_manager.async_load()
            assert area_manager.areas == {}

    async def test_async_load_with_data(self, area_manager: AreaManager, mock_area_data):
        """Test loading with existing data."""
        storage_data = {
            "opentherm_gateway_id": "gateway1",
            "global_eco_temp": 18.0,
            "global_comfort_temp": 21.0,
            "areas": [mock_area_data],  # List, not dict
        }

        with patch.object(
            area_manager._persistence_service._store, "async_load", return_value=storage_data
        ):
            await area_manager.async_load()
            assert area_manager.opentherm_gateway_id == "gateway1"
            assert area_manager.opentherm_gateway_id == "gateway1"
            assert area_manager.global_eco_temp == 18.0
            assert TEST_AREA_ID in area_manager.areas

    async def test_async_load_with_global_settings(self, area_manager: AreaManager):
        """Test loading global settings."""
        storage_data = {
            "global_away_temp": 16.0,
            "global_eco_temp": 18.0,
            "global_comfort_temp": 21.0,
            "global_home_temp": 20.0,
            "global_sleep_temp": 17.0,
            "global_activity_temp": 22.0,
            "hysteresis": 0.5,
            "frost_protection_enabled": True,
            "frost_protection_temp": 5.0,
            "areas": [],  # List, not dict
        }

        with patch.object(
            area_manager._persistence_service._store, "async_load", return_value=storage_data
        ):
            await area_manager.async_load()
            assert area_manager.global_away_temp == 16.0
            assert area_manager.global_eco_temp == 18.0
            assert area_manager.global_comfort_temp == 21.0
            assert area_manager.global_home_temp == 20.0
            assert area_manager.global_sleep_temp == 17.0
            assert area_manager.global_activity_temp == 22.0
            assert area_manager.hysteresis == 0.5
            assert area_manager.frost_protection_enabled is True
            assert area_manager.frost_protection_temp == 5.0


class TestAreaManagerSaving:
    """Test AreaManager saving to storage."""

    async def test_async_save(self, area_manager: AreaManager, mock_area_data):
        """Test saving to storage."""
        # Initialize safety_sensors to avoid AttributeError
        area_manager._safety_service._safety_sensors = []

        # Add an area
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area_manager.areas[TEST_AREA_ID] = area

        with patch.object(
            area_manager._persistence_service._store, "async_save", new=AsyncMock()
        ) as mock_save:
            await area_manager.async_save()
            mock_save.assert_called_once()

            # Verify saved data structure
            saved_data = mock_save.call_args[0][0]
            assert "areas" in saved_data
            assert isinstance(saved_data["areas"], list)
            assert len(saved_data["areas"]) == 1
            # The 'opentherm_enabled' flag was removed; presence of gateway_id implies control enabled
            assert "opentherm_gateway_id" in saved_data
            assert "global_eco_temp" in saved_data

    async def test_async_save_empty_areas(self, area_manager: AreaManager):
        """Test saving with no areas."""
        # Initialize safety_sensors to avoid AttributeError
        area_manager._safety_service._safety_sensors = []

        with patch.object(
            area_manager._persistence_service._store, "async_save", new=AsyncMock()
        ) as mock_save:
            await area_manager.async_save()
            mock_save.assert_called_once()

            saved_data = mock_save.call_args[0][0]
            assert saved_data["areas"] == []


class TestAreaRetrieval:
    """Test area retrieval operations."""

    def test_get_area_exists(self, area_manager: AreaManager, mock_area_data):
        """Test getting an existing area."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area_manager.areas[TEST_AREA_ID] = area

        result = area_manager.get_area(TEST_AREA_ID)
        assert result == area
        assert result.name == TEST_AREA_NAME

    def test_get_area_not_exists(self, area_manager: AreaManager):
        """Test getting a non-existent area."""
        result = area_manager.get_area("nonexistent")
        assert result is None

    def test_get_all_areas(self, area_manager: AreaManager, mock_area_data):
        """Test getting all areas."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area_manager.areas[TEST_AREA_ID] = area

        all_areas = area_manager.get_all_areas()
        assert len(all_areas) == 1
        assert TEST_AREA_ID in all_areas
        assert all_areas[TEST_AREA_ID] == area

    def test_get_all_areas_empty(self, area_manager: AreaManager):
        """Test getting all areas when none exist."""
        all_areas = area_manager.get_all_areas()
        assert all_areas == {}


class TestAreaOperations:
    """Test area operations (enable/disable, temperature, devices)."""

    def test_enable_area(self, area_manager: AreaManager, mock_area_data):
        """Test enabling an area."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area.enabled = False
        area_manager.areas[TEST_AREA_ID] = area

        area_manager.enable_area(TEST_AREA_ID)
        assert area.enabled is True

    def test_disable_area(self, area_manager: AreaManager, mock_area_data):
        """Test disabling an area."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area.enabled = True
        area_manager.areas[TEST_AREA_ID] = area

        area_manager.disable_area(TEST_AREA_ID)
        assert area.enabled is False

    def test_update_area_temperature(self, area_manager: AreaManager, mock_area_data):
        """Test updating area current temperature."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area_manager.areas[TEST_AREA_ID] = area

        area_manager.update_area_temperature(TEST_AREA_ID, 22.5)
        assert area.current_temperature == 22.5

    def test_set_area_target_temperature(self, area_manager: AreaManager, mock_area_data):
        """Test setting area target temperature."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area_manager.areas[TEST_AREA_ID] = area

        area_manager.set_area_target_temperature(TEST_AREA_ID, 21.0)
        assert area.target_temperature == 21.0

    def test_add_device_to_area(self, area_manager: AreaManager, mock_area_data):
        """Test adding a device to an area."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area_manager.areas[TEST_AREA_ID] = area

        area_manager.add_device_to_area(TEST_AREA_ID, "climate.new_device", "thermostat")
        assert "climate.new_device" in area.devices

    def test_remove_device_from_area(self, area_manager: AreaManager, mock_area_data):
        """Test removing a device from an area."""
        area = Area.from_dict(mock_area_data)
        area.area_manager = area_manager
        area_manager.areas[TEST_AREA_ID] = area
        area.add_device("climate.test_device", "thermostat")

        area_manager.remove_device_from_area(TEST_AREA_ID, "climate.test_device")
        assert "climate.test_device" not in area.devices

    def test_operation_on_nonexistent_area_raises(self, area_manager: AreaManager):
        """Test that operations on non-existent area raise ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            area_manager.enable_area("nonexistent")

        with pytest.raises(ValueError, match="does not exist"):
            area_manager.disable_area("nonexistent")

        with pytest.raises(ValueError, match="does not exist"):
            area_manager.update_area_temperature("nonexistent", 20.0)

        with pytest.raises(ValueError, match="does not exist"):
            area_manager.set_area_target_temperature("nonexistent", 20.0)

        with pytest.raises(ValueError, match="does not exist"):
            area_manager.add_device_to_area("nonexistent", "device.id", "type")


class TestGlobalSettings:
    """Test global settings management."""

    async def test_set_opentherm_gateway(self, area_manager: AreaManager):
        """Test setting OpenTherm gateway."""
        await area_manager.set_opentherm_gateway("gateway1")
        assert area_manager.opentherm_gateway_id == "gateway1"

    async def test_set_opentherm_gateway_disabled(self, area_manager: AreaManager):
        """Test setting OpenTherm gateway disabled."""
        # Setting gateway id to a value enables control; control is determined by gateway presence
        await area_manager.set_opentherm_gateway("gateway1")
        assert area_manager.opentherm_gateway_id == "gateway1"

    def test_global_preset_temperatures(self, area_manager: AreaManager):
        """Test global preset temperature defaults."""
        assert area_manager.global_eco_temp == DEFAULT_ECO_TEMP
        assert area_manager.global_comfort_temp == DEFAULT_COMFORT_TEMP
        assert area_manager.global_away_temp == DEFAULT_AWAY_TEMP

    def test_global_settings_persistence(self, area_manager: AreaManager):
        """Test that global settings can be modified."""
        area_manager.global_eco_temp = 17.0
        area_manager.global_comfort_temp = 22.0
        area_manager.frost_protection_enabled = True
        area_manager.frost_protection_temp = 7.0

        assert area_manager.global_eco_temp == 17.0
        assert area_manager.global_comfort_temp == 22.0
        assert area_manager.frost_protection_enabled is True
        assert area_manager.frost_protection_temp == 7.0


class TestOldSafetySensorMigration:
    """Test migration from old safety sensor format."""

    async def test_load_old_safety_sensor_format(self, hass: HomeAssistant):
        """Test loading old single safety sensor format and migration."""
        area_manager = AreaManager(hass)

        old_format_data = {
            "areas": {},
            "safety_sensor_id": "binary_sensor.smoke",
            "safety_sensor_attribute": "smoke",
            "safety_sensor_alert_value": True,
            "safety_sensor_enabled": True,
        }

        with patch.object(
            area_manager._persistence_service._store, "async_load", return_value=old_format_data
        ):
            await area_manager.async_load()

        # Should migrate to new format
        assert len(area_manager._safety_service._safety_sensors) == 1
        assert area_manager._safety_service._safety_sensors[0]["sensor_id"] == "binary_sensor.smoke"
        assert area_manager._safety_service._safety_sensors[0]["attribute"] == "smoke"
        assert area_manager._safety_service._safety_sensors[0]["alert_value"] is True
        assert area_manager._safety_service._safety_sensors[0]["enabled"] is True

    async def test_load_new_safety_sensor_format(self, hass: HomeAssistant):
        """Test loading new multi-sensor format."""
        area_manager = AreaManager(hass)

        new_format_data = {
            "areas": {},
            "safety_sensors": [
                {
                    "sensor_id": "binary_sensor.smoke",
                    "attribute": "smoke",
                    "alert_value": True,
                    "enabled": True,
                },
                {
                    "sensor_id": "binary_sensor.co",
                    "attribute": "carbon_monoxide",
                    "alert_value": True,
                    "enabled": True,
                },
            ],
        }

        with patch.object(
            area_manager._persistence_service._store, "async_load", return_value=new_format_data
        ):
            await area_manager.async_load()

        # Should load new format directly
        assert len(area_manager._safety_service._safety_sensors) == 2


class TestSafetySensorManagement:
    """Test safety sensor management."""

    def test_add_safety_sensor(self, area_manager: AreaManager):
        """Test adding a safety sensor."""
        area_manager.add_safety_sensor(
            "binary_sensor.smoke", attribute="smoke", alert_value=True, enabled=True
        )

        assert len(area_manager._safety_service._safety_sensors) == 1
        assert area_manager._safety_service._safety_sensors[0]["sensor_id"] == "binary_sensor.smoke"

    def test_add_safety_sensor_updates_existing(self, area_manager: AreaManager):
        """Test adding safety sensor updates existing one."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "smoke", True, True)
        area_manager.add_safety_sensor("binary_sensor.smoke", "state", "alarm", False)

        assert len(area_manager._safety_service._safety_sensors) == 1
        assert area_manager._safety_service._safety_sensors[0]["attribute"] == "state"
        assert area_manager._safety_service._safety_sensors[0]["alert_value"] == "alarm"
        assert area_manager._safety_service._safety_sensors[0]["enabled"] is False

    def test_remove_safety_sensor(self, area_manager: AreaManager):
        """Test removing a safety sensor."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "smoke", True, True)
        area_manager.add_safety_sensor("binary_sensor.co", "carbon_monoxide", True, True)

        area_manager.remove_safety_sensor("binary_sensor.smoke")

        assert len(area_manager._safety_service._safety_sensors) == 1
        assert area_manager._safety_service._safety_sensors[0]["sensor_id"] == "binary_sensor.co"

    def test_remove_last_safety_sensor_clears_alert(self, area_manager: AreaManager):
        """Test removing last sensor clears alert."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "smoke", True, True)
        area_manager._safety_service._safety_alert_active = True

        area_manager.remove_safety_sensor("binary_sensor.smoke")

        assert len(area_manager._safety_service._safety_sensors) == 0
        assert area_manager._safety_service._safety_alert_active is False

    def test_get_safety_sensors(self, area_manager: AreaManager):
        """Test getting safety sensors."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "smoke", True, True)

        sensors = area_manager.get_safety_sensors()

        assert len(sensors) == 1
        assert sensors[0]["sensor_id"] == "binary_sensor.smoke"
        # Should return a copy
        sensors.append({"test": "data"})
        assert len(area_manager._safety_service._safety_sensors) == 1

    def test_check_safety_sensor_status_no_sensors(self, area_manager: AreaManager):
        """Test checking status with no sensors."""
        is_alert, sensor_id = area_manager.check_safety_sensor_status()

        assert is_alert is False
        assert sensor_id is None

    def test_check_safety_sensor_status_alert(self, hass: HomeAssistant, area_manager: AreaManager):
        """Test checking status with sensor in alert."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "smoke", True, True)

        # Mock sensor state
        hass.states.async_set("binary_sensor.smoke", "on", {"smoke": True})

        is_alert, sensor_id = area_manager.check_safety_sensor_status()

        assert is_alert is True
        assert sensor_id == "binary_sensor.smoke"

    def test_check_safety_sensor_status_state_attribute(
        self, hass: HomeAssistant, area_manager: AreaManager
    ):
        """Test checking status using state attribute."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "state", "alarm", True)

        # Mock sensor state
        hass.states.async_set("binary_sensor.smoke", "alarm", {})

        is_alert, sensor_id = area_manager.check_safety_sensor_status()

        assert is_alert is True
        assert sensor_id == "binary_sensor.smoke"

    def test_check_safety_sensor_status_disabled_sensor(
        self, hass: HomeAssistant, area_manager: AreaManager
    ):
        """Test checking status skips disabled sensors."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "smoke", True, False)

        # Mock sensor state in alert
        hass.states.async_set("binary_sensor.smoke", "on", {"smoke": True})

        is_alert, sensor_id = area_manager.check_safety_sensor_status()

        # Should skip disabled sensor
        assert is_alert is False
        assert sensor_id is None

    def test_safety_alert_active_status(self, area_manager: AreaManager):
        """Test safety alert active status."""
        assert area_manager.is_safety_alert_active() is False

        area_manager.set_safety_alert_active(True)

        assert area_manager.is_safety_alert_active() is True

    def test_set_safety_alert_active_logs_change(self, area_manager: AreaManager):
        """Test setting safety alert logs state changes."""
        # First change
        area_manager.set_safety_alert_active(True)
        assert area_manager._safety_service._safety_alert_active is True

        # Same value shouldn't trigger change
        area_manager.set_safety_alert_active(True)
        assert area_manager._safety_service._safety_alert_active is True

        # Different value triggers change
        area_manager.set_safety_alert_active(False)
        assert area_manager._safety_service._safety_alert_active is False


class TestScheduleManagement:
    """Test schedule management."""

    def test_add_schedule_to_area(self, area_manager: AreaManager):
        """Test adding schedule to area."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area_manager.areas[TEST_AREA_ID] = area

        schedule = area_manager.add_schedule_to_area(
            TEST_AREA_ID, "schedule1", "08:00", 21.0, [0, 1, 2]
        )

        assert schedule.schedule_id == "schedule1"
        assert schedule.time == "08:00"
        assert schedule.temperature == 21.0
        assert schedule.days == [0, 1, 2]
        assert "schedule1" in area.schedules

    def test_add_schedule_to_nonexistent_area(self, area_manager: AreaManager):
        """Test adding schedule to non-existent area raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            area_manager.add_schedule_to_area("nonexistent", "schedule1", "08:00", 21.0, [0])

    def test_remove_schedule_from_area(self, area_manager: AreaManager):
        """Test removing schedule from area."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area_manager.areas[TEST_AREA_ID] = area

        area_manager.add_schedule_to_area(TEST_AREA_ID, "schedule1", "08:00", 21.0, [0])
        area_manager.remove_schedule_from_area(TEST_AREA_ID, "schedule1")

        assert "schedule1" not in area.schedules

    def test_remove_schedule_from_nonexistent_area(self, area_manager: AreaManager):
        """Test removing schedule from non-existent area raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            area_manager.remove_schedule_from_area("nonexistent", "schedule1")


class TestDeviceManagement:
    """Test device management."""

    def test_remove_device_from_area(self, area_manager: AreaManager):
        """Test removing device from area."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.add_device("device.id", "climate", None)
        area_manager.areas[TEST_AREA_ID] = area

        area_manager.remove_device_from_area(TEST_AREA_ID, "device.id")

        assert "device.id" not in area.devices

    def test_remove_device_from_nonexistent_area(self, area_manager: AreaManager):
        """Test removing device from non-existent area raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            area_manager.remove_device_from_area("nonexistent", "device.id")


class TestTRVSettings:
    """Test TRV temperature settings."""

    def test_set_trv_temperatures(self, area_manager: AreaManager):
        """Test setting TRV temperatures."""
        area_manager.set_trv_temperatures(25.0, 10.0)

        assert area_manager.trv_heating_temp == 25.0
        assert area_manager.trv_idle_temp == 10.0

    def test_set_trv_temperatures_with_offset(self, area_manager: AreaManager):
        """Test setting TRV temperatures with offset."""
        area_manager.set_trv_temperatures(25.0, 10.0, 5.0)

        assert area_manager.trv_heating_temp == 25.0
        assert area_manager.trv_idle_temp == 10.0
        assert area_manager.trv_temp_offset == 5.0


class TestDeviceEventLogging:
    """Test device event logging functionality."""

    def test_async_add_device_event(self, area_manager: AreaManager):
        """Test adding a device event."""
        from smart_heating.models.device_event import DeviceEvent

        event = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="set_temperature",
            payload={"temperature": 21.0},
            status="ok",
        )

        area_manager.async_add_device_event(TEST_AREA_ID, event)

        # Check event was added
        assert TEST_AREA_ID in area_manager._device_service._device_logs
        assert len(area_manager._device_service._device_logs[TEST_AREA_ID]) == 1
        assert area_manager._device_service._device_logs[TEST_AREA_ID][0] == event

    def test_async_add_device_event_creates_deque(self, area_manager: AreaManager):
        """Test that adding event creates deque if it doesn't exist."""
        from smart_heating.models.device_event import DeviceEvent

        event = DeviceEvent.now(
            area_id="new_area",
            device_id="climate.test",
            direction="sent",
            command_type="test",
            payload={},
        )

        area_manager.async_add_device_event("new_area", event)

        assert "new_area" in area_manager._device_service._device_logs

    def test_async_add_device_event_with_listener(self, area_manager: AreaManager):
        """Test that event listeners are notified."""
        from unittest.mock import Mock

        from smart_heating.models.device_event import DeviceEvent

        listener = Mock()
        area_manager.add_device_log_listener(listener)

        event = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="test",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, event)

        # Listener should be called with event dict
        listener.assert_called_once()
        call_args = listener.call_args[0][0]
        assert call_args["area_id"] == TEST_AREA_ID
        assert call_args["device_id"] == "climate.test"

    async def test_async_add_device_event_with_async_listener(
        self, hass: HomeAssistant, area_manager: AreaManager
    ):
        """Test that async event listeners are notified."""
        from smart_heating.models.device_event import DeviceEvent

        calls = []

        async def async_listener(event_dict):
            calls.append(event_dict)

        area_manager.add_device_log_listener(async_listener)

        event = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="test",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, event)
        await hass.async_block_till_done()

        # Async listener should be called
        assert len(calls) == 1
        assert calls[0]["area_id"] == TEST_AREA_ID

    def test_async_add_device_event_retention(self, area_manager: AreaManager):
        """Test that old events are purged based on retention."""
        from datetime import datetime, timedelta, timezone

        from smart_heating.models.device_event import DeviceEvent

        # Create old event (older than retention period)
        old_timestamp = (
            (datetime.now(timezone.utc) - timedelta(minutes=120)).isoformat().replace("+00:00", "Z")
        )
        old_event = DeviceEvent(
            timestamp=old_timestamp,
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="old_command",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, old_event)

        # Create new event
        new_event = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="new_command",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, new_event)

        # Old event should be purged
        logs = area_manager._device_service._device_logs[TEST_AREA_ID]
        assert len(logs) == 1
        assert logs[0].command_type == "new_command"

    def test_async_get_device_logs_empty(self, area_manager: AreaManager):
        """Test getting logs for area with no logs."""
        logs = area_manager.async_get_device_logs(TEST_AREA_ID)
        assert logs == []

    def test_async_get_device_logs(self, area_manager: AreaManager):
        """Test getting device logs."""
        from smart_heating.models.device_event import DeviceEvent

        event1 = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test1",
            direction="sent",
            command_type="command1",
            payload={},
        )
        event2 = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test2",
            direction="received",
            command_type="command2",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, event1)
        area_manager.async_add_device_event(TEST_AREA_ID, event2)

        logs = area_manager.async_get_device_logs(TEST_AREA_ID)

        assert len(logs) == 2

    def test_async_get_device_logs_filter_by_device(self, area_manager: AreaManager):
        """Test filtering logs by device ID."""
        from smart_heating.models.device_event import DeviceEvent

        event1 = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test1",
            direction="sent",
            command_type="command1",
            payload={},
        )
        event2 = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test2",
            direction="sent",
            command_type="command2",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, event1)
        area_manager.async_add_device_event(TEST_AREA_ID, event2)

        logs = area_manager.async_get_device_logs(TEST_AREA_ID, device_id="climate.test1")

        assert len(logs) == 1
        assert logs[0]["device_id"] == "climate.test1"

    def test_async_get_device_logs_filter_by_direction(self, area_manager: AreaManager):
        """Test filtering logs by direction."""
        from smart_heating.models.device_event import DeviceEvent

        event1 = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="command1",
            payload={},
        )
        event2 = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="received",
            command_type="command2",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, event1)
        area_manager.async_add_device_event(TEST_AREA_ID, event2)

        logs = area_manager.async_get_device_logs(TEST_AREA_ID, direction="sent")

        assert len(logs) == 1
        assert logs[0]["direction"] == "sent"

    def test_async_get_device_logs_filter_by_since(self, area_manager: AreaManager):
        """Test filtering logs by timestamp."""
        from datetime import datetime, timedelta, timezone

        from smart_heating.models.device_event import DeviceEvent

        # Create events with different timestamps
        old_timestamp = (
            (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
        )
        old_event = DeviceEvent(
            timestamp=old_timestamp,
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="old_command",
            payload={},
        )

        new_event = DeviceEvent.now(
            area_id=TEST_AREA_ID,
            device_id="climate.test",
            direction="sent",
            command_type="new_command",
            payload={},
        )

        area_manager.async_add_device_event(TEST_AREA_ID, old_event)
        area_manager.async_add_device_event(TEST_AREA_ID, new_event)

        # Filter to only get events from 15 minutes ago
        since = (
            (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
        )
        logs = area_manager.async_get_device_logs(TEST_AREA_ID, since=since)

        assert len(logs) == 1
        assert logs[0]["command_type"] == "new_command"

    def test_add_device_log_listener(self, area_manager: AreaManager):
        """Test adding device log listener."""
        from unittest.mock import Mock

        listener = Mock()
        area_manager.add_device_log_listener(listener)

        assert listener in area_manager._device_service._device_log_listeners

    def test_add_device_log_listener_idempotent(self, area_manager: AreaManager):
        """Test adding same listener multiple times is idempotent."""
        from unittest.mock import Mock

        listener = Mock()
        area_manager.add_device_log_listener(listener)
        area_manager.add_device_log_listener(listener)

        # Should only be added once
        assert area_manager._device_service._device_log_listeners.count(listener) == 1

    def test_remove_device_log_listener(self, area_manager: AreaManager):
        """Test removing device log listener."""
        from unittest.mock import Mock

        listener = Mock()
        area_manager.add_device_log_listener(listener)
        area_manager.remove_device_log_listener(listener)

        assert listener not in area_manager._device_service._device_log_listeners

    def test_remove_device_log_listener_silent_if_not_present(self, area_manager: AreaManager):
        """Test removing listener that doesn't exist is silent."""
        from unittest.mock import Mock

        listener = Mock()
        # Should not raise
        area_manager.remove_device_log_listener(listener)


class TestSafetySensorAdditional:
    """Additional safety sensor tests for edge cases."""

    def test_clear_safety_sensors(self, area_manager: AreaManager):
        """Test clearing all safety sensors."""
        area_manager.add_safety_sensor("binary_sensor.smoke", "smoke", True, True)
        area_manager.add_safety_sensor("binary_sensor.co", "carbon_monoxide", True, True)
        area_manager._safety_service._safety_alert_active = True

        area_manager.clear_safety_sensors()

        assert len(area_manager._safety_service._safety_sensors) == 0
        assert area_manager._safety_service._safety_alert_active is False

    def test_check_safety_sensor_status_sensor_not_found(
        self, hass: HomeAssistant, area_manager: AreaManager
    ):
        """Test checking status when sensor entity not found."""
        area_manager.add_safety_sensor("binary_sensor.missing", "smoke", True, True)

        # Don't set any state - sensor won't be found
        is_alert, sensor_id = area_manager.check_safety_sensor_status()

        # Should return False when sensor not found
        assert is_alert is False
        assert sensor_id is None


class TestOpenThermGatewayAutoEnable:
    """Test auto-enabling features when OpenTherm gateway is set."""

    async def test_set_opentherm_gateway_auto_enables_features(self, area_manager: AreaManager):
        """Test that setting gateway auto-enables advanced control and heating curve."""
        # Ensure features are initially disabled
        area_manager.advanced_control_enabled = False
        area_manager.heating_curve_enabled = False

        await area_manager.set_opentherm_gateway("gateway1")

        # Should auto-enable features
        assert area_manager.advanced_control_enabled is True
        assert area_manager.heating_curve_enabled is True

    async def test_set_opentherm_gateway_already_enabled(self, area_manager: AreaManager):
        """Test setting gateway when features already enabled."""
        # Pre-enable features
        area_manager.advanced_control_enabled = True
        area_manager.heating_curve_enabled = True

        await area_manager.set_opentherm_gateway("gateway1")

        # Should remain enabled
        assert area_manager.advanced_control_enabled is True
        assert area_manager.heating_curve_enabled is True


class TestAdvancedControlLoading:
    """Test loading advanced control settings from storage."""

    async def test_async_load_with_advanced_control_settings(self, area_manager: AreaManager):
        """Test loading advanced control settings."""
        storage_data = {
            "areas": [],
            "advanced_control_enabled": True,
            "heating_curve_enabled": True,
            "pwm_enabled": True,
            "overshoot_protection_enabled": True,
            "default_heating_curve_coefficient": 1.5,
        }

        with patch.object(
            area_manager._persistence_service._store, "async_load", return_value=storage_data
        ):
            await area_manager.async_load()

            assert area_manager.advanced_control_enabled is True
            assert area_manager.heating_curve_enabled is True
            assert area_manager.pwm_enabled is True
            assert area_manager.overshoot_protection_enabled is True
            assert area_manager.default_heating_curve_coefficient == 1.5
