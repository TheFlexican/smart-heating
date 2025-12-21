"""Tests for TRV backend handlers and history recording."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.api.handlers.sensors import (
    handle_get_trv_candidates,
    handle_add_trv_entity,
    handle_remove_trv_entity,
)


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {
        "smart_heating": {
            "entry_id_123": MagicMock(data={}, async_request_refresh=AsyncMock()),
            "history": MagicMock(),
            "climate_controller": MagicMock(),
            "schedule_executor": MagicMock(),
        }
    }
    return hass


@pytest.fixture
def mock_area_manager():
    manager = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_area():
    area = MagicMock()
    area.area_id = "living_room"
    area.add_trv_entity = MagicMock()
    area.remove_trv_entity = MagicMock()
    return area


class TestTrvCandidatesAndConfig:
    @pytest.mark.asyncio
    async def test_get_trv_candidates(self, mock_hass):
        sensor_state = MagicMock()
        sensor_state.state = "42"
        sensor_state.attributes = {"friendly_name": "TRV Position", "unit_of_measurement": "%"}

        binary_state = MagicMock()
        binary_state.state = "on"
        binary_state.attributes = {"friendly_name": "TRV Open", "device_class": "opening"}

        mock_hass.states.async_entity_ids = MagicMock(
            side_effect=lambda domain: {
                "sensor": ["sensor.trv_position"],
                "binary_sensor": ["binary_sensor.trv_open"],
            }.get(domain, [])
        )

        mock_hass.states.get = MagicMock(
            side_effect=lambda entity_id: {
                "sensor.trv_position": sensor_state,
                "binary_sensor.trv_open": binary_state,
            }.get(entity_id)
        )

        response = await handle_get_trv_candidates(mock_hass)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert "entities" in body
        assert any(e["entity_id"] == "sensor.trv_position" for e in body["entities"])
        assert any(e["entity_id"] == "binary_sensor.trv_open" for e in body["entities"])

    @pytest.mark.asyncio
    async def test_add_and_remove_trv_entity(self, mock_hass, mock_area_manager, mock_area):
        mock_area_manager.get_area.return_value = mock_area

        data = {"entity_id": "sensor.trv_position", "role": "position", "name": "Living Room TRV"}

        response = await handle_add_trv_entity(mock_hass, mock_area_manager, "living_room", data)
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert body["entity_id"] == "sensor.trv_position"

        mock_area.add_trv_entity.assert_called_once_with(
            "sensor.trv_position", role="position", name="Living Room TRV"
        )
        mock_area_manager.async_save.assert_called_once()
        mock_hass.data["smart_heating"]["entry_id_123"].async_request_refresh.assert_called_once()

        # Test remove
        response = await handle_remove_trv_entity(
            mock_hass, mock_area_manager, "living_room", "sensor.trv_position"
        )
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True

        mock_area.remove_trv_entity.assert_called_once_with("sensor.trv_position")
        mock_area_manager.async_save.assert_called()
        mock_hass.data["smart_heating"]["entry_id_123"].async_request_refresh.assert_called()
