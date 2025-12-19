from unittest.mock import MagicMock

import pytest
from smart_heating.const import DOMAIN
from smart_heating.features.opentherm_logger import OpenThermLogger
from smart_heating.api.websocket import websocket_get_areas, websocket_subscribe_updates


def test_opentherm_logger_basic():
    hass = MagicMock()
    ot_logger = OpenThermLogger(hass)

    # Boiler ON with setpoint and counts
    ot_logger.log_boiler_control(
        state="ON",
        setpoint=55.123,
        heating_areas=["a1", "a2"],
        max_target_temp=56.7,
        overhead=2.0,
        floor_heating_count=1,
        radiator_count=2,
    )

    # OFF
    ot_logger.log_boiler_control(state="OFF")

    # Zone demand
    ot_logger.log_zone_demand("a1", "Living", True, 20.3, 22.0)

    # Modulation
    ot_logger.log_modulation(modulation_level=45.5, flame_on=True, ch_water_temp=60.0)

    # Gateway info with capabilities
    caps = {"feature": True}
    ot_logger.log_gateway_info("gateway_1", True, available=True, capabilities=caps)

    logs = ot_logger.get_logs()
    assert len(logs) >= 4

    # Gateway capabilities accessible
    gcaps = ot_logger.get_gateway_capabilities()
    assert gcaps.get("feature") is True

    # Clear logs
    ot_logger.clear_logs()
    assert ot_logger.get_logs() == []


@pytest.mark.asyncio
async def test_async_discover_mqtt_capabilities():
    # Use MagicMock hass so we can stub states.get
    hass = MagicMock()
    # Case: missing entity
    hass.states.get = MagicMock(return_value=None)
    ot_logger = OpenThermLogger(hass)
    caps = await ot_logger.async_discover_mqtt_capabilities("gateway.missing")
    assert caps == {}

    # Case: found entity with attributes
    class MockState:
        def __init__(self):
            self._state = "on"
            self.attributes = {"boiler_water_temp": 60.0, "modulation_level": 45.0}

        @property
        def state(self):
            return self._state

    hass.states.get = MagicMock(return_value=MockState())
    caps = await ot_logger.async_discover_mqtt_capabilities("gateway.present")
    assert "attributes" in caps
    assert "boiler_water_temp" in caps["attributes"]


def make_connection():
    conn = MagicMock()
    conn.subscriptions = {}
    conn.send_error = MagicMock()
    conn.send_result = MagicMock()
    conn.send_message = MagicMock()
    return conn


def test_websocket_subscribe_not_loaded():
    hass = MagicMock()
    hass.data.setdefault(DOMAIN, {})

    conn = make_connection()
    msg = {"id": "1"}

    websocket_subscribe_updates(hass, conn, msg)
    conn.send_error.assert_called_once()


def test_websocket_subscribe_and_forward(monkeypatch):
    hass = MagicMock()

    # Fake coordinator with async_add_listener
    coordinator = MagicMock()
    coordinator.data = {"areas": {"a1": {"target_temperature": 21}}}

    def add_listener(cb):
        # Immediately invoke the callback to simulate an update
        cb()
        return lambda: None

    coordinator.async_add_listener = add_listener

    hass.data = {DOMAIN: {"entry1": coordinator}}

    conn = make_connection()
    msg = {"id": "2"}

    websocket_subscribe_updates(hass, conn, msg)

    # Should have stored a subscription
    assert "2" in conn.subscriptions
    conn.send_result.assert_called_once()


def test_websocket_get_areas_not_loaded():
    hass = MagicMock()
    hass.data.setdefault(DOMAIN, {})

    conn = make_connection()
    msg = {"id": "3"}
    websocket_get_areas(hass, conn, msg)
    conn.send_error.assert_called_once()


def test_websocket_get_areas_success():
    hass = MagicMock()
    # Create area and area manager
    area = MagicMock()
    area.area_id = "a1"
    area.name = "Living"
    area.enabled = True
    area.state = "heating"
    area.target_temperature = 21.0
    area.current_temperature = 20.0
    area.devices = {"thermo1": {"type": "thermostat"}}
    area.schedules = {}
    area.night_boost_enabled = False
    area.night_boost_offset = 0
    area.night_boost_start_time = None
    area.night_boost_end_time = None
    area.smart_boost_enabled = False
    area.smart_boost_target_time = None
    area.weather_entity_id = None
    area.preset_mode = None
    area.away_temp = None
    area.eco_temp = None
    area.comfort_temp = None
    area.home_temp = None
    area.sleep_temp = None
    area.activity_temp = None
    area.boost_mode_active = False
    area.boost_temp = None
    area.boost_duration = None
    area.hvac_mode = None
    area.window_sensors = []
    area.presence_sensors = []

    area_manager = MagicMock()
    area_manager.get_all_areas.return_value = {"a1": area}

    coordinator = MagicMock()
    coordinator.area_manager = area_manager

    hass.data = {DOMAIN: {"entry1": coordinator}}

    # Provide a thermostat state
    state = MagicMock()
    state.state = "on"
    state.attributes = {
        "current_temperature": 20.0,
        "temperature": 21.0,
        "hvac_action": "heating",
        "friendly_name": "Thermo 1",
    }
    hass.states.get = MagicMock(return_value=state)

    conn = make_connection()
    msg = {"id": "4"}
    websocket_get_areas(hass, conn, msg)
    conn.send_result.assert_called_once()
