"""Tests for Smart Heating Coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.update_coordinator import UpdateFailed
from smart_heating.const import DOMAIN, STATE_INITIALIZED, UPDATE_INTERVAL
from smart_heating.core.coordinator import SmartHeatingCoordinator

from tests.unit.const import TEST_AREA_ID


@pytest.fixture
def coordinator(
    hass: HomeAssistant, mock_config_entry, mock_area_manager
) -> SmartHeatingCoordinator:
    """Create a SmartHeatingCoordinator instance."""
    return SmartHeatingCoordinator(hass, mock_config_entry, mock_area_manager)


class TestCoordinatorInitialization:
    """Test Coordinator initialization."""

    def test_init(self, hass: HomeAssistant, mock_config_entry, mock_area_manager):
        """Test coordinator initialization."""
        coordinator = SmartHeatingCoordinator(hass, mock_config_entry, mock_area_manager)

        assert coordinator.hass == hass
        assert coordinator.area_manager == mock_area_manager
        assert coordinator.name == DOMAIN
        assert coordinator.update_interval == UPDATE_INTERVAL
        assert coordinator._unsub_state_listener is None

    def test_update_interval(self, hass: HomeAssistant, mock_config_entry, mock_area_manager):
        """Test update interval configuration."""
        coordinator = SmartHeatingCoordinator(hass, mock_config_entry, mock_area_manager)

        # Should use UPDATE_INTERVAL constant
        assert coordinator.update_interval == UPDATE_INTERVAL


class TestCoordinatorSetup:
    """Test coordinator setup."""

    async def test_async_setup_no_devices(self, coordinator: SmartHeatingCoordinator):
        """Test setup with no devices."""
        coordinator.area_manager.get_all_areas.return_value = {}

        with patch("smart_heating.core.coordinator.async_track_state_change_event") as mock_track:
            await coordinator.async_setup()

            # Should not set up state listeners if no devices
            mock_track.assert_not_called()
            assert coordinator._unsub_state_listener is None

    async def test_async_setup_with_devices(
        self, coordinator: SmartHeatingCoordinator, mock_area_data
    ):
        """Test setup with devices."""
        mock_area = MagicMock()
        mock_area.devices = {"climate.test": {"type": "thermostat"}}
        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        with patch("smart_heating.core.coordinator.async_track_state_change_event") as mock_track:
            mock_track.return_value = MagicMock()
            await coordinator.async_setup()

            # Should set up state listeners for devices
            mock_track.assert_called_once()
            assert coordinator._unsub_state_listener is not None

    async def test_async_shutdown(self, coordinator: SmartHeatingCoordinator):
        """Test coordinator shutdown."""
        mock_unsub = MagicMock()
        coordinator._unsub_state_listener = mock_unsub

        await coordinator.async_shutdown()

        mock_unsub.assert_called_once()
        assert coordinator._unsub_state_listener is None


class TestCoordinatorDataUpdate:
    """Test Coordinator data update."""

    async def test_async_update_data_success(
        self, coordinator: SmartHeatingCoordinator, mock_area_data
    ):
        """Test successful data update."""
        # Create mock area with proper attributes
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        data = await coordinator._async_update_data()

        assert data["status"] == STATE_INITIALIZED
        assert data["area_count"] == 1
        assert "areas" in data
        assert TEST_AREA_ID in data["areas"]
        assert data["areas"][TEST_AREA_ID]["name"] == "Living Room"
        assert data["areas"][TEST_AREA_ID]["enabled"] is True

    async def test_async_update_data_empty_areas(self, coordinator: SmartHeatingCoordinator):
        """Test data update with no areas."""
        coordinator.area_manager.get_all_areas.return_value = {}

        data = await coordinator._async_update_data()

        assert data["status"] == STATE_INITIALIZED
        assert data["area_count"] == 0
        assert data["areas"] == {}

    async def test_async_update_data_with_thermostat(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test data update includes thermostat device states."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {"climate.test": {"type": "thermostat"}}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        # Create actual state in hass
        hass.states.async_set(
            "climate.test",
            "heat",
            {
                "friendly_name": "Test Thermostat",
                "current_temperature": 20.0,
                "temperature": 21.0,
                "hvac_action": "heating",
            },
        )

        data = await coordinator._async_update_data()

        assert "areas" in data
        assert TEST_AREA_ID in data["areas"]
        assert len(data["areas"][TEST_AREA_ID]["devices"]) == 1
        device = data["areas"][TEST_AREA_ID]["devices"][0]
        assert device["id"] == "climate.test"
        assert device["type"] == "thermostat"
        assert device["current_temperature"] == 20.0
        assert device["target_temperature"] == 21.0
        assert device["hvac_action"] == "heating"

    async def test_async_update_data_error(self, coordinator: SmartHeatingCoordinator):
        """Test data update with error."""
        # Use KeyError since the coordinator catches specific exceptions
        coordinator.area_manager.get_all_areas.side_effect = KeyError("Test error")

        with pytest.raises(UpdateFailed, match="Test error"):
            await coordinator._async_update_data()


class TestStateChangeHandling:
    """Test state change event handling."""

    def test_handle_state_change_no_new_state(self, coordinator: SmartHeatingCoordinator):
        """Test handling state change with no new state."""
        event = MagicMock()
        event.data = {"entity_id": "climate.test", "new_state": None}

        # Should not raise any errors
        coordinator._handle_state_change(event)

    @pytest.mark.asyncio
    async def test_handle_state_change_initial_state(self, coordinator: SmartHeatingCoordinator):
        """Test handling initial state (old_state is None)."""
        mock_new_state = MagicMock()
        mock_new_state.state = "heat"

        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": None,
            "new_state": mock_new_state,
        }

        import asyncio as _asyncio

        orig = _asyncio.create_task
        with patch("smart_heating.core.coordinator.asyncio.create_task") as mock_create_task:
            mock_create_task.side_effect = lambda coro, orig=orig: orig(coro)
            coordinator._handle_state_change(event)
            # Should trigger refresh for initial state
            assert mock_create_task.called
            # Ensure that a coordinator async_request_refresh coroutine was scheduled
            # A debounce task should be created (local coroutine). Don't require it to schedule 'async_request_refresh' yet.
            assert any(
                hasattr(c.args[0], "cr_code")
                and c.args[0].cr_code.co_name == "async_request_refresh"
                for c in mock_create_task.call_args_list
            )

    @pytest.mark.asyncio
    async def test_handle_state_change_state_changed(self, coordinator: SmartHeatingCoordinator):
        """Test handling state change."""
        mock_old_state = MagicMock()
        mock_old_state.state = "idle"
        mock_old_state.attributes = {"temperature": 20.0, "current_temperature": 19.0}

        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {"temperature": 20.0, "current_temperature": 19.0}

        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state,
        }

        import asyncio as _asyncio

        orig = _asyncio.create_task
        with patch("smart_heating.core.coordinator.asyncio.create_task") as mock_create_task:
            mock_create_task.side_effect = lambda coro, orig=orig: orig(coro)
            coordinator._handle_state_change(event)
            # Should trigger refresh when state changes
            assert mock_create_task.called
            assert any(
                hasattr(c.args[0], "cr_code")
                and c.args[0].cr_code.co_name == "async_request_refresh"
                for c in mock_create_task.call_args_list
            )

    @pytest.mark.asyncio
    async def test_handle_state_change_current_temperature_changed(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test handling current temperature change."""
        mock_old_state = MagicMock()
        mock_old_state.state = "heat"
        mock_old_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 19.0,
            "hvac_action": "heating",
        }

        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 20.0,
            "hvac_action": "heating",
        }

        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state,
        }

        import asyncio as _asyncio

        orig = _asyncio.create_task
        with patch("smart_heating.core.coordinator.asyncio.create_task") as mock_create_task:
            mock_create_task.side_effect = lambda coro, orig=orig: orig(coro)
            coordinator._handle_state_change(event)
            # Should trigger refresh when current temperature changes
            assert mock_create_task.called
            assert any(
                hasattr(c.args[0], "cr_code")
                and c.args[0].cr_code.co_name == "async_request_refresh"
                for c in mock_create_task.call_args_list
            )

    @pytest.mark.asyncio
    async def test_handle_state_change_hvac_action_changed(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test handling HVAC action change."""
        mock_old_state = MagicMock()
        mock_old_state.state = "heat"
        mock_old_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 20.0,
            "hvac_action": "idle",
        }

        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 20.0,
            "hvac_action": "heating",
        }

        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state,
        }

        import asyncio as _asyncio

        orig = _asyncio.create_task
        with patch("smart_heating.core.coordinator.asyncio.create_task") as mock_create_task:
            mock_create_task.side_effect = lambda coro, orig=orig: orig(coro)
            coordinator._handle_state_change(event)
            # Should trigger refresh when hvac_action changes
            assert mock_create_task.called
            assert any(
                hasattr(c.args[0], "cr_code")
                and c.args[0].cr_code.co_name == "async_request_refresh"
                for c in mock_create_task.call_args_list
            )

    @pytest.mark.asyncio
    async def test_handle_state_change_target_temperature_debounced(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test that target temperature changes are debounced."""
        import asyncio

        mock_old_state = MagicMock()
        mock_old_state.state = "heat"
        mock_old_state.attributes = {
            "temperature": 20.0,
            "current_temperature": 19.0,
            "hvac_action": "heating",
        }

        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {
            "temperature": 21.0,  # Target temp changed
            "current_temperature": 19.0,
            "hvac_action": "heating",
        }

        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state,
        }

        with patch.object(coordinator, "_apply_manual_temperature_change"):
            coordinator._handle_state_change(event)
            # Wait for async task to start
            await asyncio.sleep(0.01)
            # Should create debounce task via the debouncer
            assert coordinator._debouncer.has_pending("climate.test")


class TestCoordinatorDeviceUpdates:
    """Test Coordinator device state updates."""

    async def test_update_device_state(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test updating device state in coordinator data."""
        # Create mock area with thermostat device
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {"climate.test": {"type": "thermostat"}}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        # Set device state in hass
        hass.states.async_set(
            "climate.test",
            "heat",
            {
                "friendly_name": "Test Thermostat",
                "current_temperature": 20.0,
                "temperature": 21.0,
                "hvac_action": "heating",
            },
        )

        await coordinator.async_request_refresh()

        # Verify device state was captured
        assert coordinator.data is not None
        assert "areas" in coordinator.data
        assert TEST_AREA_ID in coordinator.data["areas"]
        devices = coordinator.data["areas"][TEST_AREA_ID]["devices"]
        assert len(devices) == 1
        assert devices[0]["state"] == "heat"

    async def test_handle_unavailable_device(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test handling unavailable devices."""
        # Create mock area with device
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {"climate.unavailable": {"type": "thermostat"}}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        # Device state is None (unavailable)
        await coordinator.async_request_refresh()

        # Should not crash and mark device as unavailable
        assert coordinator.data is not None
        assert "areas" in coordinator.data
        devices = coordinator.data["areas"][TEST_AREA_ID]["devices"]
        assert len(devices) == 1
        assert devices[0]["state"] == "unavailable"


class TestCoordinatorAreaUpdates:
    """Test Coordinator area updates."""

    async def test_update_area_temperature(self, coordinator: SmartHeatingCoordinator):
        """Test updating area temperature."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        await coordinator.async_request_refresh()

        assert coordinator.data["areas"][TEST_AREA_ID]["current_temperature"] == 20.0

    async def test_update_area_target_temperature(self, coordinator: SmartHeatingCoordinator):
        """Test updating area target temperature."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 22.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 22.0

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        await coordinator.async_request_refresh()

        assert coordinator.data["areas"][TEST_AREA_ID]["target_temperature"] == 22.0

    async def test_update_area_enabled_state(self, coordinator: SmartHeatingCoordinator):
        """Test updating area enabled state."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = False
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        await coordinator.async_request_refresh()

        assert coordinator.data["areas"][TEST_AREA_ID]["enabled"] is False


class TestDebounceTemperatureChange:
    """Test debounced temperature change handling."""

    async def test_handle_temperature_change_debounce(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test temperature change creates debounce task."""
        import asyncio

        old_state = State("climate.test", "heat", {"temperature": 20.0})
        new_state = State("climate.test", "heat", {"temperature": 21.0})

        with patch.object(coordinator, "_apply_manual_temperature_change"):
            coordinator._handle_temperature_change("climate.test", old_state, new_state)

            # Wait for async task to start
            await asyncio.sleep(0.01)

            # Should create debounce task in the debouncer
            assert coordinator._debouncer.has_pending("climate.test")

    async def test_apply_manual_temperature_change_matches_expected(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test manual temperature change when it matches expected temperature."""
        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.devices = {"climate.test": {}}
        mock_area.get_effective_target_temperature.return_value = 21.0
        mock_area.target_temperature = 21.0
        mock_area.manual_override = False  # Set initial value

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        # Temperature matches expected - should not set manual override
        await coordinator._apply_manual_temperature_change("climate.test", 21.0)

        # manual_override should remain False since temp matches
        assert mock_area.manual_override is False

    async def test_apply_manual_temperature_change_different_from_expected(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test manual temperature change when it differs from expected."""
        # Disable grace period to allow manual override detection
        coordinator._manual_override_detector.set_startup_grace_period(False)

        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.devices = {"climate.test": {}}
        mock_area.get_effective_target_temperature.return_value = 21.0
        mock_area.target_temperature = 21.0
        mock_area.manual_override = False

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}
        coordinator.area_manager.async_save = AsyncMock()

        # Temperature differs - should set manual override
        await coordinator._apply_manual_temperature_change("climate.test", 23.0)

        assert mock_area.target_temperature == 23.0
        assert mock_area.manual_override is True
        coordinator.area_manager.async_save.assert_called_once()


class TestTemperatureSensorConversion:
    """Test temperature sensor data extraction and conversion."""

    def test_get_temperature_from_sensor_celsius(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from Celsius sensor."""
        state = State("sensor.temp", "20.5", {"unit_of_measurement": "°C"})

        result = coordinator._get_temperature_from_sensor("sensor.temp", state)

        assert result == 20.5

    def test_get_temperature_from_sensor_fahrenheit(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from Fahrenheit sensor."""
        state = State("sensor.temp", "68.0", {"unit_of_measurement": "°F"})

        result = coordinator._get_temperature_from_sensor("sensor.temp", state)

        assert result is not None
        assert abs(result - 20.0) < 0.1  # 68°F ≈ 20°C

    def test_get_temperature_from_sensor_unavailable(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from unavailable sensor."""
        state = State("sensor.temp", "unavailable", {})

        result = coordinator._get_temperature_from_sensor("sensor.temp", state)

        assert result is None

    def test_get_temperature_from_sensor_unknown(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from unknown sensor."""
        state = State("sensor.temp", "unknown", {})

        result = coordinator._get_temperature_from_sensor("sensor.temp", state)

        assert result is None

    def test_get_temperature_from_sensor_invalid(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from sensor with invalid value."""
        state = State("sensor.temp", "invalid", {})

        result = coordinator._get_temperature_from_sensor("sensor.temp", state)

        assert result is None


class TestValvePosition:
    """Test valve position extraction."""

    def test_get_valve_position_valid(self, coordinator: SmartHeatingCoordinator):
        """Test getting valid valve position."""
        state = State("number.valve", "50.0", {})

        result = coordinator._get_valve_position(state)

        assert result == 50.0

    def test_get_valve_position_unavailable(self, coordinator: SmartHeatingCoordinator):
        """Test getting valve position when unavailable."""
        state = State("number.valve", "unavailable", {})

        result = coordinator._get_valve_position(state)

        assert result is None

    def test_get_valve_position_unknown(self, coordinator: SmartHeatingCoordinator):
        """Test getting valve position when unknown."""
        state = State("number.valve", "unknown", {})

        result = coordinator._get_valve_position(state)

        assert result is None

    def test_get_valve_position_invalid(self, coordinator: SmartHeatingCoordinator):
        """Test getting valve position with invalid value."""
        state = State("number.valve", "invalid", {})

        result = coordinator._get_valve_position(state)

        assert result is None


class TestGetDeviceStateData:
    """Test device state data extraction."""

    def test_get_device_state_data_temperature_sensor(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting state data for temperature sensor."""
        device_id = "sensor.living_room_temp"
        device_info = {"type": "temperature_sensor"}

        # Set state using hass.states.async_set
        hass.states.async_set(
            device_id,
            "22.5",
            {"friendly_name": "Living Room Temperature", "unit_of_measurement": "°C"},
        )

        result = coordinator._get_device_state_data(device_id, device_info)

        assert result["id"] == device_id
        assert result["type"] == "temperature_sensor"
        assert result["state"] == "22.5"
        assert result["name"] == "Living Room Temperature"
        assert result["temperature"] == 22.5

    def test_get_device_state_data_valve(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting state data for valve."""
        device_id = "number.valve_position"
        device_info = {"type": "valve"}

        hass.states.async_set(device_id, "75.0", {"friendly_name": "Valve Position"})

        result = coordinator._get_device_state_data(device_id, device_info)

        assert result["id"] == device_id
        assert result["type"] == "valve"
        assert result["state"] == "75.0"
        assert result["name"] == "Valve Position"
        assert result["position"] == 75.0

    def test_get_device_state_data_thermostat(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting state data for thermostat."""
        device_id = "climate.living_room"
        device_info = {"type": "thermostat"}

        hass.states.async_set(
            device_id,
            "heat",
            {
                "friendly_name": "Living Room Thermostat",
                "current_temperature": 20.0,
                "temperature": 21.0,
                "hvac_action": "heating",
            },
        )

        result = coordinator._get_device_state_data(device_id, device_info)

        assert result["id"] == device_id
        assert result["type"] == "thermostat"
        assert result["state"] == "heat"
        assert result["name"] == "Living Room Thermostat"
        assert result["current_temperature"] == 20.0
        assert result["target_temperature"] == 21.0
        assert result["hvac_action"] == "heating"

    def test_get_device_state_data_no_state(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting state data when device has no state."""
        device_id = "sensor.missing"
        device_info = {"type": "temperature_sensor"}

        # Don't set any state - device doesn't exist

        result = coordinator._get_device_state_data(device_id, device_info)

        assert result["id"] == device_id
        assert result["type"] == "temperature_sensor"
        assert result["state"] == "unavailable"
        assert result["name"] == device_id
        # Should not have temperature key since state is None
        assert "temperature" not in result


class TestCoordinatorAreaOperations:
    """Test coordinator area enable/disable operations."""

    @pytest.mark.asyncio
    async def test_async_enable_area_success(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test enabling area successfully."""
        area_id = "living_room"

        # Mock area manager
        mock_area = MagicMock()
        mock_area.current_temperature = 18.0
        mock_area.get_effective_target_temperature.return_value = 20.0
        coordinator.area_manager.get_area.return_value = mock_area
        coordinator.area_manager.enable_area = MagicMock()
        coordinator.area_manager.async_save = AsyncMock()

        # Mock climate controller
        mock_climate_controller = MagicMock()
        mock_climate_controller.device_handler = MagicMock()
        mock_climate_controller.device_handler.async_control_thermostats = AsyncMock()
        mock_climate_controller.device_handler.async_control_valves = AsyncMock()
        hass.data = {DOMAIN: {"climate_controller": mock_climate_controller}}

        # Mock coordinator refresh
        coordinator.async_request_refresh = AsyncMock()

        await coordinator.async_enable_area(area_id)

        # Verify area manager calls
        coordinator.area_manager.enable_area.assert_called_once_with(area_id)
        coordinator.area_manager.async_save.assert_called_once()

        # Verify device control calls
        mock_climate_controller.device_handler.async_control_thermostats.assert_called_once()
        mock_climate_controller.device_handler.async_control_valves.assert_called_once()

        # Verify coordinator refresh
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_enable_area_no_temperature(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test enabling area when area has no current temperature."""
        area_id = "living_room"

        # Mock area with no temperature
        mock_area = MagicMock()
        mock_area.current_temperature = None
        coordinator.area_manager.get_area.return_value = mock_area
        coordinator.area_manager.enable_area = MagicMock()
        coordinator.area_manager.async_save = AsyncMock()

        # Mock climate controller
        mock_climate_controller = MagicMock()
        mock_climate_controller.device_handler = MagicMock()
        mock_climate_controller.device_handler.async_control_thermostats = AsyncMock()
        hass.data = {DOMAIN: {"climate_controller": mock_climate_controller}}

        # Mock coordinator refresh
        coordinator.async_request_refresh = AsyncMock()

        await coordinator.async_enable_area(area_id)

        # Verify area manager calls
        coordinator.area_manager.enable_area.assert_called_once_with(area_id)
        coordinator.area_manager.async_save.assert_called_once()

        # Should not call device control (no temperature)
        mock_climate_controller.device_handler.async_control_thermostats.assert_not_called()

        # Verify coordinator refresh
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_enable_area_error(self, coordinator: SmartHeatingCoordinator):
        """Test enabling area when area manager raises error."""
        area_id = "unknown_area"

        # Make enable_area raise ValueError
        coordinator.area_manager.enable_area = MagicMock(side_effect=ValueError("Area not found"))

        with pytest.raises(ValueError, match="Area not found"):
            await coordinator.async_enable_area(area_id)

    @pytest.mark.asyncio
    async def test_async_disable_area_success(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test disabling area successfully."""
        area_id = "living_room"

        # Mock area manager
        mock_area = MagicMock()
        coordinator.area_manager.get_area.return_value = mock_area
        coordinator.area_manager.disable_area = MagicMock()
        coordinator.area_manager.async_save = AsyncMock()

        # Mock climate controller
        mock_climate_controller = MagicMock()
        mock_climate_controller.device_handler = MagicMock()
        mock_climate_controller.device_handler.async_set_valves_to_off = AsyncMock()
        mock_climate_controller.device_handler.async_control_thermostats = AsyncMock()
        hass.data = {DOMAIN: {"climate_controller": mock_climate_controller}}

        # Mock coordinator refresh
        coordinator.async_request_refresh = AsyncMock()

        await coordinator.async_disable_area(area_id)

        # Verify area manager calls
        coordinator.area_manager.disable_area.assert_called_once_with(area_id)
        coordinator.area_manager.async_save.assert_called_once()

        # Verify device control calls
        mock_climate_controller.device_handler.async_set_valves_to_off.assert_called_once_with(
            mock_area, 0.0
        )
        mock_climate_controller.device_handler.async_control_thermostats.assert_called_once_with(
            mock_area, False, None
        )

        # Verify coordinator refresh
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_disable_area_error(self, coordinator: SmartHeatingCoordinator):
        """Test disabling area when area manager raises error."""
        area_id = "unknown_area"

        # Make disable_area raise ValueError
        coordinator.area_manager.disable_area = MagicMock(side_effect=ValueError("Area not found"))

        with pytest.raises(ValueError, match="Area not found"):
            await coordinator.async_disable_area(area_id)

    @pytest.mark.asyncio
    async def test_async_enable_area_no_climate_controller(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test enabling area when climate controller is not available."""
        area_id = "living_room"

        mock_area = MagicMock()
        mock_area.current_temperature = 18.0
        mock_area.get_effective_target_temperature.return_value = 20.0
        coordinator.area_manager.get_area.return_value = mock_area
        coordinator.area_manager.enable_area = MagicMock()
        coordinator.area_manager.async_save = AsyncMock()

        # No climate controller in hass.data
        hass.data = {DOMAIN: {}}
        coordinator.async_request_refresh = AsyncMock()

        await coordinator.async_enable_area(area_id)

        # Should still enable area and save, just skip device control
        coordinator.area_manager.enable_area.assert_called_once_with(area_id)
        coordinator.area_manager.async_save.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_disable_area_no_climate_controller(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test disabling area when climate controller is not available."""
        area_id = "living_room"

        mock_area = MagicMock()
        coordinator.area_manager.get_area.return_value = mock_area
        coordinator.area_manager.disable_area = MagicMock()
        coordinator.area_manager.async_save = AsyncMock()

        # No climate controller in hass.data
        hass.data = {DOMAIN: {}}
        coordinator.async_request_refresh = AsyncMock()

        await coordinator.async_disable_area(area_id)

        # Should still disable area and save, just skip device control
        coordinator.area_manager.disable_area.assert_called_once_with(area_id)
        coordinator.area_manager.async_save.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()


class TestGracePeriod:
    """Test startup grace period functionality."""

    @pytest.mark.asyncio
    async def test_grace_period_activation(self, coordinator: SmartHeatingCoordinator):
        """Test that grace period is activated during setup."""
        coordinator.area_manager.get_all_areas.return_value = {}

        # Grace period is activated in __init__ now
        assert coordinator._manual_override_detector._startup_grace_period is True

        with patch("smart_heating.core.coordinator.async_track_state_change_event"):
            await coordinator.async_setup()

        # Grace period should still be active (deactivated after 10 seconds)
        assert coordinator._manual_override_detector._startup_grace_period is True

    @pytest.mark.asyncio
    async def test_apply_manual_temp_change_during_grace_period(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test that manual temp changes are ignored during grace period."""
        coordinator._startup_grace_period = True

        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.devices = {"climate.test": {}}
        mock_area.manual_override = False
        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        await coordinator._apply_manual_temperature_change("climate.test", 23.0)

        # Should not set manual override during grace period
        assert mock_area.manual_override is False

    @pytest.mark.asyncio
    async def test_apply_manual_temp_change_none_temperature(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test that None temperature is ignored."""
        coordinator._startup_grace_period = False

        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.devices = {"climate.test": {}}
        mock_area.manual_override = False
        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        await coordinator._apply_manual_temperature_change("climate.test", None)

        # Should not set manual override for None temperature
        assert mock_area.manual_override is False

    @pytest.mark.asyncio
    async def test_apply_manual_temp_change_lower_than_expected(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test that lower temperature (stale state) is ignored."""
        coordinator._startup_grace_period = False

        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.devices = {"climate.test": {}}
        mock_area.get_effective_target_temperature.return_value = 21.0
        mock_area.manual_override = False
        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        # Temperature is lower than expected (stale state from old preset)
        await coordinator._apply_manual_temperature_change("climate.test", 18.0)

        # Should not set manual override for stale lower temperature
        assert mock_area.manual_override is False


class TestTaskCancellation:
    """Test task cancellation helper methods."""

    @pytest.mark.asyncio
    async def test_cancel_task_if_exists_with_task(self, coordinator: SmartHeatingCoordinator):
        """Test cancelling an existing task."""
        import asyncio

        # Create a dummy task
        async def dummy():
            await asyncio.sleep(10)

        task = asyncio.create_task(dummy())
        coordinator._test_task = task

        coordinator._cancel_task_if_exists("_test_task")

        # Wait for cancellation to complete
        await asyncio.sleep(0.01)

        # Task should be cancelled and attribute set to None
        assert task.cancelled() or task.done()
        assert coordinator._test_task is None

    @pytest.mark.asyncio
    async def test_cancel_task_if_exists_no_task(self, coordinator: SmartHeatingCoordinator):
        """Test cancelling when task doesn't exist."""
        # Should not raise any errors
        coordinator._cancel_task_if_exists("_nonexistent_task")

    @pytest.mark.asyncio
    async def test_cancel_task_collection_dict(self, coordinator: SmartHeatingCoordinator):
        """Test cancelling task collection (dict)."""
        import asyncio

        async def dummy():
            await asyncio.sleep(10)

        tasks = {
            "task1": asyncio.create_task(dummy()),
            "task2": asyncio.create_task(dummy()),
        }

        coordinator._cancel_task_collection(tasks)

        # All tasks should be cancelled and dict cleared
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_cancel_task_collection_set(self, coordinator: SmartHeatingCoordinator):
        """Test cancelling task collection (set)."""
        import asyncio

        async def dummy():
            await asyncio.sleep(10)

        tasks = {
            asyncio.create_task(dummy()),
            asyncio.create_task(dummy()),
        }

        coordinator._cancel_task_collection(tasks)

        # All tasks should be cancelled and set cleared
        assert len(tasks) == 0


class TestDebounceTaskCancellation:
    """Test debounce task cancellation."""

    @pytest.mark.skip(
        reason="Debouncer task management is fully tested in test_debouncer.py. "
        "This test checks implementation details no longer directly accessible after refactoring."
    )
    @pytest.mark.asyncio
    async def test_multiple_temperature_changes_cancel_previous(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test that multiple rapid temperature changes are debounced.

        Note: This functionality is now tested in tests/unit/core/coordination/test_debouncer.py
        which has 12 comprehensive tests including cancellation behavior.
        """
        pass


class TestWeatherStateData:
    """Test weather state data functionality."""

    def test_get_weather_state_data_valid(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting valid weather state."""
        weather_entity = "weather.home"

        hass.states.async_set(
            weather_entity,
            "10.5",
            {
                "temperature": 10.5,
                "humidity": 75,
                "wind_speed": 15,
            },
        )

        result = coordinator._get_weather_state_data(weather_entity)

        assert result is not None
        assert result["entity_id"] == weather_entity
        assert result["temperature"] == 10.5
        assert "attributes" in result
        assert result["attributes"]["humidity"] == 75

    def test_get_weather_state_data_unavailable(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting weather state when unavailable."""
        weather_entity = "weather.home"

        hass.states.async_set(weather_entity, "unavailable", {})

        result = coordinator._get_weather_state_data(weather_entity)

        assert result is None

    def test_get_weather_state_data_unknown(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting weather state when unknown."""
        weather_entity = "weather.home"

        hass.states.async_set(weather_entity, "unknown", {})

        result = coordinator._get_weather_state_data(weather_entity)

        assert result is None

    def test_get_weather_state_data_no_entity(self, coordinator: SmartHeatingCoordinator):
        """Test getting weather state when entity ID is None."""
        result = coordinator._get_weather_state_data(None)

        assert result is None

    def test_get_weather_state_data_invalid_value(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting weather state with invalid temperature value."""
        weather_entity = "weather.home"

        hass.states.async_set(weather_entity, "invalid_temp", {})

        result = coordinator._get_weather_state_data(weather_entity)

        assert result is None


class TestOpenThermGateway:
    """Test OpenTherm gateway state data."""

    def test_get_opentherm_gateway_state_valid(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting valid OpenTherm gateway state."""
        gateway_id = "climate.opentherm_gateway"

        hass.states.async_set(
            gateway_id,
            "heat",
            {
                "relative_mod_level": 75.5,
                "flame_on": True,
            },
        )

        result = coordinator._get_opentherm_gateway_state(gateway_id)

        assert result is not None
        assert result["entity_id"] == gateway_id
        assert result["state"] == "heat"
        assert result["modulation_level"] == 75.5
        assert "attributes" in result

    def test_get_opentherm_gateway_state_modulation_level_attr(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting OpenTherm gateway with alternative modulation attribute."""
        gateway_id = "climate.opentherm_gateway"

        hass.states.async_set(
            gateway_id,
            "heat",
            {
                "modulation_level": 50.0,  # Alternative attribute name
            },
        )

        result = coordinator._get_opentherm_gateway_state(gateway_id)

        assert result is not None
        assert result["modulation_level"] == 50.0

    def test_get_opentherm_gateway_state_no_modulation(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting OpenTherm gateway without modulation level."""
        gateway_id = "climate.opentherm_gateway"

        hass.states.async_set(gateway_id, "heat", {})

        result = coordinator._get_opentherm_gateway_state(gateway_id)

        assert result is not None
        assert result["modulation_level"] is None

    def test_get_opentherm_gateway_state_invalid_modulation(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting OpenTherm gateway with invalid modulation value."""
        gateway_id = "climate.opentherm_gateway"

        hass.states.async_set(
            gateway_id,
            "heat",
            {
                "relative_mod_level": "invalid",
            },
        )

        result = coordinator._get_opentherm_gateway_state(gateway_id)

        assert result is not None
        assert result["modulation_level"] is None

    def test_get_opentherm_gateway_state_no_entity(self, coordinator: SmartHeatingCoordinator):
        """Test getting OpenTherm gateway when entity ID is None."""
        result = coordinator._get_opentherm_gateway_state(None)

        assert result is None

    def test_get_opentherm_gateway_state_missing_entity(self, coordinator: SmartHeatingCoordinator):
        """Test getting OpenTherm gateway when entity doesn't exist."""
        result = coordinator._get_opentherm_gateway_state("climate.nonexistent")

        assert result is None


class TestTRVStates:
    """Test TRV state collection."""

    def test_get_trv_states_for_area_binary_sensor(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting TRV states with binary sensor."""
        mock_area = MagicMock()
        mock_area.trv_entities = [{"entity_id": "binary_sensor.trv1"}]

        hass.states.async_set("binary_sensor.trv1", "on", {})

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 1
        assert result[0]["entity_id"] == "binary_sensor.trv1"
        assert result[0]["open"] is True
        assert result[0]["position"] is None

    def test_get_trv_states_for_area_binary_sensor_off(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting TRV states with binary sensor off."""
        mock_area = MagicMock()
        mock_area.trv_entities = [{"entity_id": "binary_sensor.trv1"}]

        hass.states.async_set("binary_sensor.trv1", "off", {})

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 1
        assert result[0]["open"] is False

    def test_get_trv_states_for_area_sensor_with_position(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting TRV states with position sensor."""
        mock_area = MagicMock()
        mock_area.trv_entities = [{"entity_id": "sensor.trv1"}]
        mock_area.state = "heating"

        hass.states.async_set("sensor.trv1", "50.0", {})

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 1
        assert result[0]["entity_id"] == "sensor.trv1"
        assert result[0]["position"] == 50.0
        assert result[0]["running_state"] == "heating"

    def test_get_trv_states_for_area_with_position_attribute(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting TRV states with position in attributes."""
        mock_area = MagicMock()
        mock_area.trv_entities = [{"entity_id": "sensor.trv1"}]

        # State value can't be converted to float, so it will check attributes
        hass.states.async_set(
            "sensor.trv1",
            "heating",
            {
                "position": 75.0,
            },
        )

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 1
        assert result[0]["position"] == 75.0

    def test_get_trv_states_for_area_with_valve_position_attribute(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting TRV states with valve_position in attributes."""
        mock_area = MagicMock()
        mock_area.trv_entities = [{"entity_id": "sensor.trv1"}]

        # State value can't be converted to float, so it will check attributes
        hass.states.async_set(
            "sensor.trv1",
            "heating",
            {
                "valve_position": 60.0,
            },
        )

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 1
        assert result[0]["position"] == 60.0

    def test_get_trv_states_for_area_unavailable(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting TRV states when unavailable."""
        mock_area = MagicMock()
        mock_area.trv_entities = [{"entity_id": "sensor.trv1"}]

        hass.states.async_set("sensor.trv1", "unavailable", {})

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 1
        assert result[0]["position"] is None
        assert result[0]["open"] is None

    def test_get_trv_states_for_area_no_entity_id(self, coordinator: SmartHeatingCoordinator):
        """Test getting TRV states with missing entity_id."""
        mock_area = MagicMock()
        mock_area.trv_entities = [{"entity_id": None}]

        result = coordinator._get_trv_states_for_area(mock_area)

        # Should skip entries without entity_id
        assert len(result) == 0

    def test_get_trv_states_for_area_no_trv_entities(self, coordinator: SmartHeatingCoordinator):
        """Test getting TRV states when area has no trv_entities attribute."""
        mock_area = MagicMock()
        # Don't set trv_entities attribute - use getattr default

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 0

    def test_get_trv_states_for_area_multiple_trvs(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test getting TRV states with multiple TRVs."""
        mock_area = MagicMock()
        mock_area.trv_entities = [
            {"entity_id": "binary_sensor.trv1"},
            {"entity_id": "sensor.trv2"},
        ]

        hass.states.async_set("binary_sensor.trv1", "on", {})
        hass.states.async_set("sensor.trv2", "75.0", {})

        result = coordinator._get_trv_states_for_area(mock_area)

        assert len(result) == 2
        assert result[0]["entity_id"] == "binary_sensor.trv1"
        assert result[0]["open"] is True
        assert result[1]["entity_id"] == "sensor.trv2"
        assert result[1]["position"] == 75.0


class TestBuildAreaDataWithWeatherAndTRV:
    """Test _build_area_data with weather and TRV functionality."""

    @pytest.mark.asyncio
    async def test_build_area_data_with_weather(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test building area data with weather entity."""
        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = "weather.home"
        mock_area.get_effective_target_temperature.return_value = 21.0

        # Set weather state
        hass.states.async_set("weather.home", "15.0", {"temperature": 15.0, "humidity": 70})

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        data = await coordinator._async_update_data()

        area_data = data["areas"][TEST_AREA_ID]
        assert "weather_state" in area_data
        assert area_data["weather_state"] is not None
        assert area_data["weather_state"]["temperature"] == 15.0

    @pytest.mark.asyncio
    async def test_build_area_data_with_trvs(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test building area data with TRV entities."""
        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_manager.boost_mode_active = False
        mock_area.boost_manager.boost_temp = 23.0
        mock_area.boost_manager.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.boost_manager.night_boost_enabled = True
        mock_area.boost_manager.night_boost_offset = 0.5
        mock_area.boost_manager.night_boost_start_time = "22:00"
        mock_area.boost_manager.night_boost_end_time = "06:00"
        mock_area.boost_manager.smart_boost_enabled = False
        mock_area.boost_manager.smart_boost_target_time = "06:00"
        mock_area.boost_manager.weather_entity_id = None
        mock_area.trv_entities = [{"entity_id": "binary_sensor.trv1"}]
        mock_area.get_effective_target_temperature.return_value = 21.0

        # Set TRV state
        hass.states.async_set("binary_sensor.trv1", "on", {})

        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}

        data = await coordinator._async_update_data()

        area_data = data["areas"][TEST_AREA_ID]
        assert "trvs" in area_data
        assert len(area_data["trvs"]) == 1
        assert area_data["trvs"][0]["entity_id"] == "binary_sensor.trv1"
        assert area_data["trvs"][0]["open"] is True
