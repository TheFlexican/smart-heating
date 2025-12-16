from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from smart_heating.const import DOMAIN, STATE_INITIALIZED
from smart_heating.sensor import (
    AreaCurrentConsumptionSensor,
    SmartHeatingStatusSensor,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(domain=DOMAIN, data={"name": "SH"}, entry_id="ent1")


def test_status_sensor_basic(mock_coordinator, mock_entry):
    sensor = SmartHeatingStatusSensor(mock_coordinator, mock_entry)
    # no data -> default initialized
    mock_coordinator.data = {}
    assert sensor.native_value == STATE_INITIALIZED

    mock_coordinator.data = {"status": "running", "area_count": 3}
    assert sensor.native_value == "running"
    attrs = sensor.extra_state_attributes
    assert attrs["integration"] == "smart_heating"
    assert attrs["area_count"] == 3
    # availability follows coordinator flag
    mock_coordinator.last_update_success = True
    assert sensor.available is True


def test_area_current_consumption_various(mock_coordinator, mock_hass, mock_entry):
    area = MagicMock()
    area.area_id = "a1"
    # without gateway
    mock_coordinator.area_manager.opentherm_gateway_id = None
    s = AreaCurrentConsumptionSensor(mock_coordinator, mock_entry, area)
    s.hass = mock_hass
    assert s.native_value is None

    # with gateway but no state
    am = mock_coordinator.area_manager
    am.opentherm_gateway_id = "gateway.1"
    hass_local = MagicMock()
    hass_local.states = MagicMock()
    hass_local.states.get = MagicMock(return_value=None)
    s.hass = hass_local
    assert s.native_value is None

    # with modulation as relative_mod_level
    state = MagicMock()
    state.attributes = {"relative_mod_level": 50}
    hass_local.states.get = MagicMock(return_value=state)
    am.default_min_consumption = 1.0
    am.default_max_consumption = 4.0
    val = s.native_value
    assert isinstance(val, float)

    # with modulation as modulation_level string
    state.attributes = {"modulation_level": "25"}
    hass_local.states.get = MagicMock(return_value=state)
    val = s.native_value
    assert isinstance(val, float)
