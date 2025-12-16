"""Tests for safety sensor API handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from smart_heating.api_handlers.config import (
    handle_get_safety_sensor,
    handle_remove_safety_sensor,
    handle_set_safety_sensor,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    from smart_heating.const import DOMAIN

    safety_mock = MagicMock()
    safety_mock.async_reconfigure = AsyncMock()
    hass.data = {DOMAIN: {"safety_monitor": safety_mock}}
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    return hass


@pytest.fixture
def mock_area_manager():
    """Create a mock AreaManager."""
    manager = MagicMock()
    manager.get_safety_sensors = MagicMock(return_value=[])
    manager.add_safety_sensor = MagicMock()
    manager.remove_safety_sensor = MagicMock()
    manager.is_safety_alert_active = MagicMock(return_value=False)
    manager.async_save = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_get_safety_sensor_empty(mock_area_manager):
    """Test getting safety sensors when none configured."""
    response = await handle_get_safety_sensor(mock_area_manager)

    assert response.status == 200
    data = response.body
    assert b'"sensors": []' in data
    assert b'"alert_active": false' in data


@pytest.mark.asyncio
async def test_get_safety_sensor_with_sensors(mock_area_manager):
    """Test getting safety sensors when configured."""
    mock_area_manager.get_safety_sensors.return_value = [
        {
            "sensor_id": "binary_sensor.smoke_detector",
            "attribute": "state",
            "alert_value": "on",
            "enabled": True,
        },
        {
            "sensor_id": "binary_sensor.opentherm_ketel_storingsindicatie",
            "attribute": "state",
            "alert_value": "on",
            "enabled": True,
        },
    ]
    mock_area_manager.is_safety_alert_active.return_value = True

    response = await handle_get_safety_sensor(mock_area_manager)

    assert response.status == 200
    data = response.body
    assert b'"alert_active": true' in data
    assert b'"sensor_id": "binary_sensor.smoke_detector"' in data


@pytest.mark.asyncio
async def test_set_safety_sensor_missing_sensor_id(mock_hass, mock_area_manager):
    """Test setting safety sensor without sensor_id."""
    data = {"attribute": "state", "alert_value": "on", "enabled": True}

    response = await handle_set_safety_sensor(mock_hass, mock_area_manager, data)

    assert response.status == 400
    assert b'"error"' in response.body


@pytest.mark.asyncio
async def test_set_safety_sensor_missing_alert_value(mock_hass, mock_area_manager):
    """Test setting safety sensor without alert_value."""
    data = {"sensor_id": "binary_sensor.smoke", "attribute": "state"}

    response = await handle_set_safety_sensor(mock_hass, mock_area_manager, data)

    assert response.status == 400
    assert b'"error"' in response.body


@pytest.mark.asyncio
async def test_set_safety_sensor_success(mock_hass, mock_area_manager):
    """Test successfully setting a safety sensor."""
    data = {
        "sensor_id": "binary_sensor.smoke_detector",
        "attribute": "state",
        "alert_value": "on",
        "enabled": True,
    }

    response = await handle_set_safety_sensor(mock_hass, mock_area_manager, data)

    assert response.status == 200
    assert b'"success": true' in response.body

    # Verify add_safety_sensor was called with correct parameters
    mock_area_manager.add_safety_sensor.assert_called_once_with(
        sensor_id="binary_sensor.smoke_detector",
        attribute="state",
        alert_value="on",
        enabled=True,
    )

    # Verify save was called
    mock_area_manager.async_save.assert_called_once()

    # Verify safety monitor reconfigure was called
    safety_monitor = mock_hass.data["smart_heating"]["safety_monitor"]
    safety_monitor.async_reconfigure.assert_called_once()

    # Verify WebSocket event was fired
    mock_hass.bus.async_fire.assert_called_once()


@pytest.mark.asyncio
async def test_set_safety_sensor_with_defaults(mock_hass, mock_area_manager):
    """Test setting safety sensor with default values."""
    data = {
        "sensor_id": "binary_sensor.opentherm_error",
        "alert_value": "on",
    }

    response = await handle_set_safety_sensor(mock_hass, mock_area_manager, data)

    assert response.status == 200

    # Verify defaults were used
    mock_area_manager.add_safety_sensor.assert_called_once_with(
        sensor_id="binary_sensor.opentherm_error",
        attribute="state",  # default
        alert_value="on",
        enabled=True,  # default
    )


@pytest.mark.asyncio
async def test_remove_safety_sensor_success(mock_hass, mock_area_manager):
    """Test successfully removing a safety sensor."""
    sensor_id = "binary_sensor.smoke_detector"

    response = await handle_remove_safety_sensor(mock_hass, mock_area_manager, sensor_id)

    assert response.status == 200
    assert b'"success": true' in response.body

    # Verify remove_safety_sensor was called
    mock_area_manager.remove_safety_sensor.assert_called_once_with(sensor_id)

    # Verify save was called
    mock_area_manager.async_save.assert_called_once()

    # Verify safety monitor reconfigure was called
    safety_monitor = mock_hass.data["smart_heating"]["safety_monitor"]
    safety_monitor.async_reconfigure.assert_called_once()

    # Verify WebSocket event was fired
    mock_hass.bus.async_fire.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_safety_sensors(mock_area_manager):
    """Test that multiple safety sensors can be configured."""
    sensors = [
        {
            "sensor_id": "binary_sensor.woonkamer_rookmelder_smoke",
            "attribute": "state",
            "alert_value": "on",
            "enabled": True,
        },
        {
            "sensor_id": "binary_sensor.opentherm_ketel_storingsindicatie",
            "attribute": "state",
            "alert_value": "on",
            "enabled": True,
        },
        {
            "sensor_id": "binary_sensor.opentherm_ketel_lage_waterdruk",
            "attribute": "state",
            "alert_value": "on",
            "enabled": True,
        },
    ]

    mock_area_manager.get_safety_sensors.return_value = sensors

    response = await handle_get_safety_sensor(mock_area_manager)

    assert response.status == 200
    data = response.body

    # Verify all sensors are in the response
    for sensor in sensors:
        assert sensor["sensor_id"].encode() in data
