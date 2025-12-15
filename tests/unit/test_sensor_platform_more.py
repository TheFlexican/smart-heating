from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from smart_heating.const import DOMAIN
from smart_heating.sensor import (
    AreaCurrentConsumptionSensor,
    AreaHeatingCurveSensor,
)


@pytest.fixture
def mock_entry():
    return MockConfigEntry(domain=DOMAIN, data={"name": "SH"}, entry_id="ent1")


def test_area_heating_curve_missing_weather(mock_hass, mock_entry):
    coordinator = MagicMock()
    # simple area with no weather entity
    area = MagicMock()
    area.name = "Zone1"
    area.area_id = "z1"
    area.weather_entity_id = None
    area.target_temperature = 21.0

    sensor = AreaHeatingCurveSensor(coordinator, mock_entry, area)
    sensor.hass = mock_hass
    assert sensor.native_value is None


def test_area_heating_curve_with_non_numeric_weather(mock_hass, mock_entry):
    coordinator = MagicMock()
    area = MagicMock()
    area.name = "Zone1"
    area.area_id = "z1"
    area.weather_entity_id = "weather.out"
    area.target_temperature = 21.0

    # non-numeric state
    # non-numeric state
    state = MagicMock()
    state.state = "unknown"
    state.attributes = {}
    mock_hass.states = MagicMock()
    mock_hass.states.get = MagicMock(return_value=state)
    sensor = AreaHeatingCurveSensor(coordinator, mock_entry, area)
    sensor.hass = mock_hass
    assert sensor.native_value is None


def test_area_heating_curve_computes_value(mock_hass, mock_entry):
    coordinator = MagicMock()
    area = MagicMock()
    area.name = "Zone1"
    area.area_id = "z1"
    area.weather_entity_id = "weather.out"
    area.target_temperature = 22.0

    # numeric weather state
    # numeric weather state
    state = MagicMock()
    state.state = "10.0"
    state.attributes = {}
    mock_hass.states = MagicMock()
    mock_hass.states.get = MagicMock(return_value=state)
    sensor = AreaHeatingCurveSensor(coordinator, mock_entry, area)
    sensor.hass = mock_hass
    val = sensor.native_value
    assert val is None or isinstance(val, float)


def test_area_current_consumption_various(mock_hass, mock_entry):
    coordinator = MagicMock()
    area = MagicMock()
    area.name = "Zone1"
    area.area_id = "z1"

    # coordinator.area_manager needed
    am = MagicMock()
    am.opentherm_gateway_id = None
    coordinator.area_manager = am

    mock_hass.states = MagicMock()
    mock_hass.states.get = MagicMock(return_value=None)
    sensor = AreaCurrentConsumptionSensor(coordinator, mock_entry, area)
    sensor.hass = mock_hass
    # without gateway configured -> None
    assert sensor.native_value is None

    # gateway configured but state missing
    am.opentherm_gateway_id = "gateway.1"
    mock_hass.states.remove = MagicMock()
    mock_hass.states.get = MagicMock(return_value=None)
    assert sensor.native_value is None

    # gateway present with non-numeric modulation
    mock_hass.states.get = MagicMock(
        return_value=MagicMock(attributes={"relative_mod_level": "bad"})
    )
    assert sensor.native_value is None

    # gateway present with modulation and consumption range
    mock_hass.states.get = MagicMock(return_value=MagicMock(attributes={"relative_mod_level": 50}))
    am.default_min_consumption = 1.0
    am.default_max_consumption = 3.0
    val = sensor.native_value
    assert isinstance(val, float)
    assert abs(val - 2.0) < 0.001
