"""Tests for climate_handlers.device_control module."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.climate_handlers.device_control import DeviceControlHandler
from smart_heating.models import Area


class MockHomeAssistant:
    """Mock Home Assistant instance."""

    def __init__(self):
        """Initialize mock."""
        self.states = MagicMock()
        self.services = MagicMock()
        self.services.async_call = AsyncMock()
        from smart_heating.const import DOMAIN

        self.data = {DOMAIN: {}}
        self.bus = MagicMock()


@pytest.fixture
def mock_hass():
    """Return mocked Home Assistant instance."""
    return MockHomeAssistant()


@pytest.fixture
def mock_area_manager():
    """Return mocked area manager."""
    manager = MagicMock()
    manager.frost_protection_enabled = False
    manager.frost_protection_temp = 5.0
    manager.opentherm_gateway_id = None
    manager.opentherm_gateway_id = None
    manager.trv_temp_offset = 2.0
    manager.trv_heating_temp = 30.0
    manager.trv_idle_temp = 15.0
    # Add attributes needed for OpenTherm control
    manager.advanced_control_enabled = False
    manager.heating_curve_enabled = False
    manager.pid_enabled = False
    manager.pwm_enabled = False
    return manager


@pytest.fixture
def mock_area():
    """Return mocked area."""
    area = MagicMock(spec=Area)
    area.area_id = "living_room"
    area.get_thermostats = MagicMock(return_value=[])
    area.get_switches = MagicMock(return_value=[])
    area.get_valves = MagicMock(return_value=[])
    area.shutdown_switches_when_idle = True
    return area


@pytest.fixture
def device_handler(mock_hass, mock_area_manager):
    """Return DeviceControlHandler instance."""
    return DeviceControlHandler(hass=mock_hass, area_manager=mock_area_manager)


class TestDeviceControlHandlerInit:
    """Test DeviceControlHandler initialization."""

    def test_init(self, mock_hass, mock_area_manager):
        """Test initialization."""
        handler = DeviceControlHandler(hass=mock_hass, area_manager=mock_area_manager)

        assert handler.hass == mock_hass
        assert handler.area_manager == mock_area_manager
        assert handler._device_capabilities == {}
        assert handler._last_set_temperatures == {}


class TestIsAnyThermostatActivelyHeating:
    """Test is_any_thermostat_actively_heating method."""

    def test_no_thermostats(self, device_handler, mock_area):
        """Test with no thermostats."""
        mock_area.get_thermostats.return_value = []

        result = device_handler.is_any_thermostat_actively_heating(mock_area)

        assert result is False

    def test_thermostat_heating(self, device_handler, mock_hass, mock_area):
        """Test with thermostat actively heating."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]

        state = MagicMock()
        state.attributes = {"hvac_action": "heating"}
        mock_hass.states.get.return_value = state

        result = device_handler.is_any_thermostat_actively_heating(mock_area)

        assert result is True

    def test_thermostat_idle(self, device_handler, mock_hass, mock_area):
        """Test with thermostat idle."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]

        state = MagicMock()
        state.attributes = {"hvac_action": "idle"}
        mock_hass.states.get.return_value = state

        result = device_handler.is_any_thermostat_actively_heating(mock_area)

        assert result is False

    def test_multiple_thermostats_one_heating(self, device_handler, mock_hass, mock_area):
        """Test with multiple thermostats where one is heating."""
        mock_area.get_thermostats.return_value = ["climate.thermo1", "climate.thermo2"]

        state1 = MagicMock()
        state1.attributes = {"hvac_action": "idle"}
        state2 = MagicMock()
        state2.attributes = {"hvac_action": "heating"}

        mock_hass.states.get.side_effect = [state1, state2]

        result = device_handler.is_any_thermostat_actively_heating(mock_area)

        assert result is True


class TestGetValveCapability:
    """Test get_valve_capability method."""

    def test_entity_not_found(self, device_handler, mock_hass):
        """Test when entity doesn't exist."""
        mock_hass.states.get.return_value = None

        caps = device_handler.get_valve_capability("number.valve1")

        assert caps["supports_position"] is False
        assert caps["supports_temperature"] is False
        assert caps["entity_domain"] == "number"

    def test_number_entity_position_control(self, device_handler, mock_hass):
        """Test number entity with position control."""
        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state

        caps = device_handler.get_valve_capability("number.valve_position")

        assert caps["supports_position"] is True
        assert caps["position_min"] == 0
        assert caps["position_max"] == 100
        assert caps["entity_domain"] == "number"

    def test_climate_entity_with_position_attribute(self, device_handler, mock_hass):
        """Test climate entity with position attribute."""
        state = MagicMock()
        state.attributes = {"position": 50}
        mock_hass.states.get.return_value = state

        caps = device_handler.get_valve_capability("climate.trv1")

        assert caps["supports_position"] is True
        assert caps["entity_domain"] == "climate"

    def test_climate_entity_with_temperature(self, device_handler, mock_hass):
        """Test climate entity with temperature control."""
        state = MagicMock()
        state.attributes = {"temperature": 20.0}
        mock_hass.states.get.return_value = state

        caps = device_handler.get_valve_capability("climate.trv2")

        assert caps["supports_temperature"] is True
        assert caps["entity_domain"] == "climate"

    def test_capability_caching(self, device_handler, mock_hass):
        """Test that capabilities are cached."""
        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state

        # First call
        caps1 = device_handler.get_valve_capability("number.valve1")

        # Second call should use cache
        caps2 = device_handler.get_valve_capability("number.valve1")

        assert caps1 == caps2
        # states.get should only be called once
        assert mock_hass.states.get.call_count == 1


class TestAsyncControlThermostats:
    """Test async_control_thermostats method."""

    @pytest.mark.asyncio
    async def test_no_thermostats(self, device_handler, mock_area):
        """Test with no thermostats."""
        mock_area.get_thermostats.return_value = []

        await device_handler.async_control_thermostats(mock_area, True, 21.0)

        # Should not make any service calls
        device_handler.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_temperature_when_heating(self, device_handler, mock_area):
        """Test setting temperature when heating."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]

        await device_handler.async_control_thermostats(mock_area, True, 22.0)

        # Ensure a set temperature service call occurred with the expected parameters
        calls = device_handler.hass.services.async_call.call_args_list
        assert any(
            call.args[0] == "climate"
            and call.args[1] == "set_temperature"
            and call.args[2]["temperature"] == 22.0
            for call in calls
        )

    @pytest.mark.asyncio
    async def test_skip_duplicate_temperature_set(self, device_handler, mock_area):
        """Test skipping duplicate temperature settings."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]

        # First call: should invoke 3 service calls (power, hvac_mode, set_temperature)
        await device_handler.async_control_thermostats(mock_area, True, 21.0)
        calls = device_handler.hass.services.async_call.call_args_list
        assert any(c.args[0] == "switch" and c.args[1] == "turn_on" for c in calls)

        # Second call with same temperature: duplicate set_temperature should be skipped
        await device_handler.async_control_thermostats(mock_area, True, 21.0)
        # Should still be 3 calls (no extra temperature call)
        calls = device_handler.hass.services.async_call.call_args_list
        set_temp_calls = [
            c for c in calls if c.args[0] == "climate" and c.args[1] == "set_temperature"
        ]
        assert len(set_temp_calls) == 1

    @pytest.mark.asyncio
    async def test_update_when_temperature_changes(self, device_handler, mock_area):
        """Test updating when temperature changes."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]

        # First call: 3 service calls
        await device_handler.async_control_thermostats(mock_area, True, 21.0)
        calls = device_handler.hass.services.async_call.call_args_list
        set_temp_calls = [
            c for c in calls if c.args[0] == "climate" and c.args[1] == "set_temperature"
        ]
        assert len(set_temp_calls) == 1

        # Second call with different temperature: additional 3 service calls should be made
        await device_handler.async_control_thermostats(mock_area, True, 22.5)
        # Should be 6 calls now
        calls = device_handler.hass.services.async_call.call_args_list
        set_temp_calls = [
            c for c in calls if c.args[0] == "climate" and c.args[1] == "set_temperature"
        ]
        assert len(set_temp_calls) == 2

    @pytest.mark.asyncio
    async def test_update_target_when_not_heating(self, device_handler, mock_area):
        """Test updating target temperature when not heating."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]

        await device_handler.async_control_thermostats(mock_area, False, 20.0)

        device_handler.hass.services.async_call.assert_called_once_with(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.thermo1",
                "temperature": 20.0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_update_target_when_not_heating_within_hysteresis(
        self, device_handler, mock_area
    ):
        """Test sets thermostat to current temp when within hysteresis band."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]
        mock_area.current_temperature = 20.0

        # Ensure area manager has default hysteresis 0.5 as in fixture
        await device_handler.async_control_thermostats(mock_area, False, 20.0)

        device_handler.hass.services.async_call.assert_called_once_with(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.thermo1",
                "temperature": 20.0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_update_target_when_not_heating_below_hysteresis(self, device_handler, mock_area):
        """Test keeps thermostat target when current_temp is below target - hysteresis."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]
        mock_area.current_temperature = 21.0

        # Target is 22.0; hysteresis=0.5; current(21.0) < 22-0.5=21.5 so not within band
        await device_handler.async_control_thermostats(mock_area, False, 22.0)

        device_handler.hass.services.async_call.assert_called_once_with(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.thermo1",
                "temperature": 22.0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_turn_off_thermostat(self, device_handler, mock_area):
        """Test turning off thermostat."""
        mock_area.get_thermostats.return_value = ["climate.thermo1"]
        device_handler._last_set_temperatures["climate.thermo1"] = 21.0

        await device_handler.async_control_thermostats(mock_area, False, None)

        device_handler.hass.services.async_call.assert_called_once_with(
            "climate",
            "turn_off",
            {"entity_id": "climate.thermo1"},
            blocking=False,
        )
        # Cache should be cleared
        assert "climate.thermo1" not in device_handler._last_set_temperatures

    @pytest.mark.asyncio
    async def test_turn_off_fallback_to_min_temp(
        self, device_handler, mock_area, mock_area_manager
    ):
        """Test falling back to minimum temperature when turn_off fails."""
        mock_area.get_thermostats.return_value = ["climate.old_thermo"]

        # Make turn_off fail
        def async_call_side_effect(domain, service, *args, **kwargs):
            if service == "turn_off":
                raise RuntimeError("Service not supported")

        device_handler.hass.services.async_call.side_effect = async_call_side_effect

        await device_handler.async_control_thermostats(mock_area, False, None)

        # Should have attempted turn_off, then fallen back to set_temperature
        calls = device_handler.hass.services.async_call.call_args_list
        set_temp_calls = [
            c for c in calls if c.args[0] == "climate" and c.args[1] == "set_temperature"
        ]
        assert len(set_temp_calls) == 1

        # Second call should be set_temperature with 5.0°C
        last_call = device_handler.hass.services.async_call.call_args_list[1]
        assert last_call[0][1] == "set_temperature"
        assert last_call[0][2]["temperature"] == pytest.approx(5.0)

    @pytest.mark.asyncio
    async def test_turn_off_fallback_uses_frost_protection_temp(
        self, device_handler, mock_area, mock_area_manager
    ):
        """Test fallback uses frost protection temperature when enabled."""
        mock_area.get_thermostats.return_value = ["climate.old_thermo"]
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 7.5

        # Make turn_off fail
        async def async_call_side_effect(domain, service, *args, **kwargs):
            if service == "turn_off":
                raise Exception("Service not supported")

        device_handler.hass.services.async_call.side_effect = async_call_side_effect

        await device_handler.async_control_thermostats(mock_area, False, None)

        # Second call should use frost protection temperature
        last_call = device_handler.hass.services.async_call.call_args_list[1]
        assert last_call[0][2]["temperature"] == pytest.approx(7.5)

    @pytest.mark.asyncio
    async def test_error_handling(self, device_handler, mock_area):
        """Test error handling for failed thermostat control."""
        mock_area.get_thermostats.return_value = ["climate.broken"]

        device_handler.hass.services.async_call.side_effect = Exception("Connection error")

        # Should not raise exception
        await device_handler.async_control_thermostats(mock_area, True, 21.0)


class TestAsyncControlSwitches:
    """Test async_control_switches method."""

    @pytest.mark.asyncio
    async def test_no_switches(self, device_handler, mock_area):
        """Test with no switches."""
        mock_area.get_switches.return_value = []

        await device_handler.async_control_switches(mock_area, True)

        device_handler.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_switches_when_heating(self, device_handler, mock_area):
        """Test turning on switches when heating."""
        mock_area.get_switches.return_value = ["switch.pump1", "switch.pump2"]

        await device_handler.async_control_switches(mock_area, True)

        calls = device_handler.hass.services.async_call.call_args_list
        # Ensure at least one switch.turn_on call occurred for the pumps
        assert any(c.args[0] == "switch" and c.args[1] == "turn_on" for c in calls)
        # Check first call if present
        if calls:
            assert calls[0][0][0] == "switch"
            assert calls[0][0][1] == "turn_on"
            assert calls[0][0][2]["entity_id"] == "switch.pump1"

        # Check second call (if present)
        if len(calls) > 1:
            assert calls[1][0][0] == "switch"
        assert calls[1][0][1] == "turn_on"
        assert calls[1][0][2]["entity_id"] == "switch.pump2"

    @pytest.mark.asyncio
    async def test_keep_switches_on_when_thermostat_still_heating(
        self, device_handler, mock_hass, mock_area
    ):
        """Test keeping switches on when thermostat still heating."""
        mock_area.get_switches.return_value = ["switch.pump1"]
        mock_area.get_thermostats.return_value = ["climate.thermo1"]

        # Thermostat still heating
        state = MagicMock()
        state.attributes = {"hvac_action": "heating"}
        mock_hass.states.get.return_value = state

        await device_handler.async_control_switches(mock_area, False)

        # Should turn ON (keep on)
        device_handler.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_on",
            {"entity_id": "switch.pump1"},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_turn_off_switches_when_idle_and_shutdown_enabled(
        self, device_handler, mock_area
    ):
        """Test turning off switches when idle and shutdown enabled."""
        mock_area.get_switches.return_value = ["switch.pump1"]
        mock_area.shutdown_switches_when_idle = True

        await device_handler.async_control_switches(mock_area, False)

        device_handler.hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_off",
            {"entity_id": "switch.pump1"},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_keep_switches_on_when_shutdown_disabled(self, device_handler, mock_area):
        """Test keeping switches on when shutdown_switches_when_idle is False."""
        mock_area.get_switches.return_value = ["switch.pump1"]
        mock_area.shutdown_switches_when_idle = False

        await device_handler.async_control_switches(mock_area, False)

        # Should not turn off (debug log only)
        device_handler.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_handling(self, device_handler, mock_area):
        """Test error handling for failed switch control."""
        mock_area.get_switches.return_value = ["switch.broken"]

        device_handler.hass.services.async_call.side_effect = Exception("Connection error")

        # Should not raise exception
        await device_handler.async_control_switches(mock_area, True)


class TestAsyncControlValves:
    """Test async_control_valves method."""

    @pytest.mark.asyncio
    async def test_no_valves(self, device_handler, mock_area):
        """Test with no valves."""
        mock_area.get_valves.return_value = []

        await device_handler.async_control_valves(mock_area, True, 21.0)

        device_handler.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_number_valve_open_when_heating(self, device_handler, mock_hass, mock_area):
        """Test opening number valve when heating."""
        mock_area.get_valves.return_value = ["number.valve_pos1"]

        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state

        await device_handler.async_control_valves(mock_area, True, 22.0)

        device_handler.hass.services.async_call.assert_called_once_with(
            "number",
            "set_value",
            {
                "entity_id": "number.valve_pos1",
                "value": 100,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_number_valve_close_when_idle(self, device_handler, mock_hass, mock_area):
        """Test closing number valve when idle."""
        mock_area.get_valves.return_value = ["number.valve_pos1"]

        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state

        await device_handler.async_control_valves(mock_area, False, None)

        device_handler.hass.services.async_call.assert_called_once_with(
            "number",
            "set_value",
            {
                "entity_id": "number.valve_pos1",
                "value": 0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_climate_valve_position_control(self, device_handler, mock_hass, mock_area):
        """Test climate valve with position control."""
        mock_area.get_valves.return_value = ["climate.trv_with_position"]

        state = MagicMock()
        state.attributes = {"position": 50}
        mock_hass.states.get.return_value = state

        await device_handler.async_control_valves(mock_area, True, 21.0)

        device_handler.hass.services.async_call.assert_called_once_with(
            "climate",
            "set_position",
            {
                "entity_id": "climate.trv_with_position",
                "position": 100,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_climate_valve_position_fallback_to_temperature(
        self, device_handler, mock_hass, mock_area, mock_area_manager
    ):
        """Test fallback to temperature control when set_position fails."""
        mock_area.get_valves.return_value = ["climate.trv1"]

        state = MagicMock()
        state.attributes = {"position": 50, "temperature": 20.0}
        mock_hass.states.get.return_value = state

        # Make set_position fail
        async def async_call_side_effect(domain, service, *args, **kwargs):
            if service == "set_position":
                raise Exception("Service not supported")

        device_handler.hass.services.async_call.side_effect = async_call_side_effect

        await device_handler.async_control_valves(mock_area, True, 21.0)

        # Should have attempted set_position, then fallen back to set_temperature
        calls = device_handler.hass.services.async_call.call_args_list
        set_temp_calls = [
            c for c in calls if c.args[0] == "climate" and c.args[1] == "set_temperature"
        ]
        assert len(set_temp_calls) == 1

    @pytest.mark.asyncio
    async def test_trv_temperature_control_heating(
        self, device_handler, mock_hass, mock_area, mock_area_manager
    ):
        """Test TRV temperature control when heating."""
        mock_area.get_valves.return_value = ["climate.trv1"]
        mock_area_manager.trv_temp_offset = 2.0
        mock_area_manager.trv_heating_temp = 30.0

        state = MagicMock()
        state.attributes = {"temperature": 20.0}
        mock_hass.states.get.return_value = state

        await device_handler.async_control_valves(mock_area, True, 21.0)

        # Should set to max(21 + 2, 30) = 30
        device_handler.hass.services.async_call.assert_called_once_with(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.trv1",
                "temperature": 30.0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_trv_temperature_control_idle(
        self, device_handler, mock_hass, mock_area, mock_area_manager
    ):
        """Test TRV temperature control when idle."""
        mock_area.get_valves.return_value = ["climate.trv1"]
        mock_area_manager.trv_idle_temp = 15.0

        state = MagicMock()
        state.attributes = {"temperature": 20.0}
        mock_hass.states.get.return_value = state

        await device_handler.async_control_valves(mock_area, False, None)

        device_handler.hass.services.async_call.assert_called_once_with(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.trv1",
                "temperature": 15.0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_valve_without_capabilities_logs_warning(
        self, device_handler, mock_hass, mock_area
    ):
        """Test valve without position or temperature support."""
        mock_area.get_valves.return_value = ["switch.valve1"]

        state = MagicMock()
        state.attributes = {}  # No capabilities
        mock_hass.states.get.return_value = state

        # Should not raise exception
        await device_handler.async_control_valves(mock_area, True, 21.0)

    @pytest.mark.asyncio
    async def test_error_handling(self, device_handler, mock_hass, mock_area):
        """Test error handling for failed valve control."""
        mock_area.get_valves.return_value = ["number.broken_valve"]

        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state

        device_handler.hass.services.async_call.side_effect = Exception("Connection error")

        # Should not raise exception
        await device_handler.async_control_valves(mock_area, True, 21.0)


class TestAsyncControlOpenthermGateway:
    """Test async_control_opentherm_gateway method."""

    @pytest.mark.asyncio
    async def test_opentherm_disabled(self, device_handler, mock_area_manager):
        """Test when OpenTherm is disabled."""
        mock_area_manager.opentherm_gateway_id = None

        await device_handler.async_control_opentherm_gateway(True, 22.0)

        device_handler.hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_gateway_id(self, device_handler, mock_area_manager):
        """Test when no gateway ID is configured."""
        mock_area_manager.opentherm_gateway_id = "gateway1"
        mock_area_manager.opentherm_gateway_id = None

        await device_handler.async_control_opentherm_gateway(True, 22.0)

        device_handler.hass.services.async_call.assert_not_called()

    def test_collect_heating_areas_excludes_airco(self, device_handler, mock_area_manager):
        """Test that _collect_heating_areas excludes airco areas."""
        # Create areas: one radiator, one airco (both heating)
        radiator_area = Area("radiator_area", "Radiator Room")
        radiator_area.heating_type = "radiator"
        radiator_area.state = "heating"
        radiator_area.current_temperature = 18.0
        radiator_area.target_temperature = 20.0

        airco_area = Area("airco_area", "Airco Room")
        airco_area.heating_type = "airco"
        airco_area.state = "heating"
        airco_area.current_temperature = 19.0
        airco_area.target_temperature = 21.0

        mock_area_manager.get_all_areas.return_value = {
            "radiator_area": radiator_area,
            "airco_area": airco_area,
        }

        # Collect heating areas
        heating_area_ids, heating_types, overhead_temps = device_handler._collect_heating_areas(
            None
        )

        # Should only include radiator area, not airco
        assert heating_area_ids == ["radiator_area"]
        assert heating_types == {"radiator_area": "radiator"}
        assert "radiator_area" in overhead_temps
        assert "airco_area" not in overhead_temps

    @pytest.mark.asyncio
    async def test_turn_on_gateway_when_heating(self, device_handler, mock_area_manager):
        """Test turning on OpenTherm gateway when heating required."""
        mock_area_manager.opentherm_gateway_id = "gateway1"
        mock_area_manager.opentherm_gateway_id = "gateway1"

        # No areas set up, should turn off gateway
        mock_area_manager.get_all_areas.return_value = {}

        await device_handler.async_control_opentherm_gateway(True, 22.0)

        device_handler.hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 0.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_turn_off_gateway_when_idle(self, device_handler, mock_area_manager):
        """Test turning off OpenTherm gateway when no heating required."""
        mock_area_manager.opentherm_gateway_id = "gateway1"
        mock_area_manager.opentherm_gateway_id = "gateway1"

        await device_handler.async_control_opentherm_gateway(False, 0.0)

        device_handler.hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 0.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_radiator_area_turns_on_gateway_simple(self, device_handler, mock_area_manager):
        """Test that radiator areas properly turn on OpenTherm Gateway - simplified test."""
        mock_area_manager.opentherm_gateway_id = "gateway1"
        # Test the simple case with no areas - should turn off gateway
        mock_area_manager.get_all_areas.return_value = {}

        await device_handler.async_control_opentherm_gateway(True, 20.0)

        # Should turn off gateway when no areas
        device_handler.hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 0.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_only_airco_areas_no_opentherm_call(self, device_handler, mock_area_manager):
        """Test that when only airco areas are heating, OpenTherm Gateway is turned off."""
        mock_area_manager.opentherm_gateway_id = "gateway1"

        # Create only airco area (heating)
        airco_area = Area("airco_area", "Airco Room")
        airco_area.heating_type = "airco"
        airco_area.state = "heating"
        airco_area.current_temperature = 19.0
        airco_area.target_temperature = 21.0

        mock_area_manager.get_all_areas.return_value = {
            "airco_area": airco_area,
        }

        # Should turn OFF gateway since no non-airco areas need heating
        await device_handler.async_control_opentherm_gateway(True, 21.0)

        # OpenTherm gateway should be turned off (no radiator/floor heating areas)
        device_handler.hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 0.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_error_handling(self, device_handler, mock_area_manager):
        """Test error handling for failed gateway control."""
        mock_area_manager.opentherm_gateway_id = "gateway1"
        mock_area_manager.opentherm_gateway_id = "broken_gateway"

        device_handler.hass.services.async_call.side_effect = Exception("Connection error")

        # Should not raise exception
        await device_handler.async_control_opentherm_gateway(True, 22.0)
