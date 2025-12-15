"""Unit tests for heating type API handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smart_heating.api_handlers.areas import handle_set_heating_type


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {"smart_heating": {}}
    return hass


@pytest.fixture
def mock_area_manager():
    """Create a mock area manager."""
    manager = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_area():
    """Create a mock area."""
    area = MagicMock()
    area.heating_type = "radiator"
    area.custom_overhead_temp = None
    return area


class TestHandleSetHeatingType:
    """Test handle_set_heating_type API handler."""

    @pytest.mark.asyncio
    async def test_set_floor_heating_type(self, mock_hass, mock_area_manager, mock_area):
        """Test setting heating type to floor_heating."""
        mock_area_manager.get_area.return_value = mock_area

        data = {"heating_type": "floor_heating"}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 200
        assert mock_area.heating_type == "floor_heating"
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_radiator_type(self, mock_hass, mock_area_manager, mock_area):
        """Test setting heating type to radiator."""
        mock_area_manager.get_area.return_value = mock_area

        data = {"heating_type": "radiator"}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 200
        assert mock_area.heating_type == "radiator"
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_custom_overhead_temp(self, mock_hass, mock_area_manager, mock_area):
        """Test setting custom overhead temperature."""
        mock_area_manager.get_area.return_value = mock_area

        data = {"custom_overhead_temp": 8.0}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 200
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_both_type_and_overhead(self, mock_hass, mock_area_manager, mock_area):
        """Test setting both heating type and custom overhead."""
        mock_area_manager.get_area.return_value = mock_area

        data = {"heating_type": "floor_heating", "custom_overhead_temp": 8.0}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 200
        assert mock_area.heating_type == "floor_heating"
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_custom_overhead(self, mock_hass, mock_area_manager, mock_area):
        """Test clearing custom overhead temperature."""
        mock_area.custom_overhead_temp = 10.0
        mock_area_manager.get_area.return_value = mock_area

        data = {"custom_overhead_temp": None}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 200
        assert mock_area.custom_overhead_temp is None
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_heating_type(self, mock_hass, mock_area_manager, mock_area):
        """Test validation rejects invalid heating type."""
        mock_area_manager.get_area.return_value = mock_area

        data = {"heating_type": "invalid_type"}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 400
        import json as _json

        body = _json.loads(response.body.decode())
        assert "error" in body
        assert "radiator" in body["error"] or "floor_heating" in body["error"]

    @pytest.mark.asyncio
    async def test_set_airco_type(self, mock_hass, mock_area_manager, mock_area):
        """Test setting heating type to airco clears radiator settings."""
        mock_area_manager.get_area.return_value = mock_area

        # Set some radiator specific settings
        mock_area.custom_overhead_temp = 10.0
        mock_area.heating_curve_coefficient = 2.0
        mock_area.hysteresis_override = 0.5

        data = {"heating_type": "airco"}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 200
        assert mock_area.heating_type == "airco"
        assert mock_area.custom_overhead_temp is None
        assert mock_area.heating_curve_coefficient is None
        assert mock_area.hysteresis_override is None

    @pytest.mark.asyncio
    async def test_overhead_temp_too_high(self, mock_hass, mock_area_manager, mock_area):
        """Test validation rejects overhead temp above 30°C."""
        mock_area_manager.get_area.return_value = mock_area

        data = {"custom_overhead_temp": 35.0}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 400
        import json as _json

        body = _json.loads(response.body.decode())
        assert "error" in body
        assert "30" in body["error"]

    @pytest.mark.asyncio
    async def test_overhead_temp_negative(self, mock_hass, mock_area_manager, mock_area):
        """Test validation rejects negative overhead temp."""
        mock_area_manager.get_area.return_value = mock_area

        data = {"custom_overhead_temp": -5.0}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "test_area", data)

        assert response.status == 400
        import json as _json

        body = _json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_area_not_found(self, mock_hass, mock_area_manager):
        """Test error when area doesn't exist."""
        mock_area_manager.get_area.return_value = None

        data = {"heating_type": "floor_heating"}
        response = await handle_set_heating_type(mock_hass, mock_area_manager, "nonexistent", data)

        assert response.status == 404
        import json as _json

        body = _json.loads(response.body.decode())
        assert "error" in body
        assert "not found" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_coordinator_refresh_triggered(self, mock_hass, mock_area_manager, mock_area):
        """Test that coordinator refresh is triggered after update."""
        mock_area_manager.get_area.return_value = mock_area
        mock_coordinator = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_hass.data["smart_heating"]["01KBZ3Q3DBWW02Y31WBHVA4T4Y"] = mock_coordinator

        data = {"heating_type": "floor_heating"}

        with patch(
            "smart_heating.api_handlers.areas.get_coordinator", return_value=mock_coordinator
        ):
            response = await handle_set_heating_type(
                mock_hass, mock_area_manager, "test_area", data
            )

        assert response.status == 200
        mock_coordinator.async_request_refresh.assert_called_once()
