from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from smart_heating.const import DOMAIN
from smart_heating.platforms.sensor import (
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

    # Mock coordinator data without weather state
    coordinator.data = {"areas": {"z1": {"weather_state": None}}}

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

    # Mock coordinator data with weather state but no temperature
    coordinator.data = {
        "areas": {
            "z1": {
                "weather_state": {"entity_id": "weather.out", "temperature": None, "attributes": {}}
            }
        }
    }

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
    area.heating_type = "radiator"

    # Mock coordinator data with numeric weather temperature
    coordinator.data = {
        "areas": {
            "z1": {
                "weather_state": {"entity_id": "weather.out", "temperature": 10.0, "attributes": {}}
            }
        }
    }

    sensor = AreaHeatingCurveSensor(coordinator, mock_entry, area)
    sensor.hass = mock_hass
    val = sensor.native_value
    assert val is not None and isinstance(val, float)


def test_area_current_consumption_various(mock_hass, mock_entry):
    coordinator = MagicMock()
    area = MagicMock()
    area.name = "Zone1"
    area.area_id = "z1"

    # coordinator.area_manager needed
    am = MagicMock()
    am.opentherm_gateway_id = None
    coordinator.area_manager = am

    # Test 1: without gateway configured -> None
    coordinator.data = None
    sensor = AreaCurrentConsumptionSensor(coordinator, mock_entry, area)
    sensor.hass = mock_hass
    assert sensor.native_value is None

    # Test 2: gateway configured but state missing in coordinator data
    am.opentherm_gateway_id = "gateway.1"
    coordinator.data = {"opentherm_gateway": None}
    assert sensor.native_value is None

    # Test 3: gateway present with non-numeric modulation
    coordinator.data = {
        "opentherm_gateway": {
            "entity_id": "gateway.1",
            "modulation_level": None,
            "state": "on",
            "attributes": {},
        }
    }
    assert sensor.native_value is None

    # Test 4: gateway present with modulation and consumption range
    coordinator.data = {
        "opentherm_gateway": {
            "entity_id": "gateway.1",
            "modulation_level": 50.0,
            "state": "on",
            "attributes": {"relative_mod_level": 50},
        }
    }
    am.default_min_consumption = 1.0
    am.default_max_consumption = 3.0
    val = sensor.native_value
    assert isinstance(val, float)
    assert abs(val - 2.0) < 0.001
