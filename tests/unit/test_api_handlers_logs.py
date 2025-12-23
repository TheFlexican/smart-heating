"""Tests for api_handlers/logs module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.api.handlers.logs import handle_get_area_logs
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_area_logger():
    """Create mock area logger."""
    logger = MagicMock()
    logger.async_get_logs = AsyncMock(
        return_value=[
            {
                "timestamp": "2024-01-01T12:00:00",
                "event_type": "temperature_change",
                "message": "Temperature changed to 21.5°C",
            },
            {
                "timestamp": "2024-01-01T11:00:00",
                "event_type": "hvac_action",
                "message": "Heating started",
            },
        ]
    )
    return logger


@pytest.fixture
def mock_hass(mock_area_logger):
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {"area_logger": mock_area_logger}}
    return hass


@pytest.fixture
def mock_request():
    """Create mock request."""
    request = MagicMock()
    request.query = {}
    return request


class TestLogsHandlers:
    """Test logs API handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_area_logs_success(self, mock_hass, mock_area_logger, mock_request):
        """Test getting area logs successfully."""
        response = await handle_get_area_logs(mock_hass, "living_room", mock_request)

        assert response.status == 200
        import json

        body = json.loads(response.body.decode())

        assert "logs" in body
        assert len(body["logs"]) == 2
        assert body["logs"][0]["event_type"] == "temperature_change"

        # Verify logger was called correctly
        mock_area_logger.async_get_logs.assert_called_once_with(
            area_id="living_room",
            limit=None,
            event_type=None,
        )

    @pytest.mark.asyncio
    async def test_handle_get_area_logs_with_limit(self, mock_hass, mock_area_logger, mock_request):
        """Test getting area logs with limit parameter."""
        mock_request.query = {"limit": "10"}

        response = await handle_get_area_logs(mock_hass, "living_room", mock_request)

        assert response.status == 200

        # Verify logger was called with limit
        mock_area_logger.async_get_logs.assert_called_once_with(
            area_id="living_room",
            limit=10,
            event_type=None,
        )

    @pytest.mark.asyncio
    async def test_handle_get_area_logs_with_type_filter(
        self, mock_hass, mock_area_logger, mock_request
    ):
        """Test getting area logs with event type filter."""
        mock_request.query = {"type": "temperature_change"}

        response = await handle_get_area_logs(mock_hass, "living_room", mock_request)

        assert response.status == 200

        # Verify logger was called with event type
        mock_area_logger.async_get_logs.assert_called_once_with(
            area_id="living_room",
            limit=None,
            event_type="temperature_change",
        )

    @pytest.mark.asyncio
    async def test_handle_get_area_logs_with_all_params(
        self, mock_hass, mock_area_logger, mock_request
    ):
        """Test getting area logs with all parameters."""
        mock_request.query = {"limit": "5", "type": "hvac_action"}

        response = await handle_get_area_logs(mock_hass, "living_room", mock_request)

        assert response.status == 200

        # Verify logger was called with all parameters
        mock_area_logger.async_get_logs.assert_called_once_with(
            area_id="living_room",
            limit=5,
            event_type="hvac_action",
        )

    @pytest.mark.asyncio
    async def test_handle_get_area_logs_no_logger(self, mock_hass, mock_request):
        """Test getting area logs when logger not available."""
        # Remove area_logger from hass.data
        mock_hass.data[DOMAIN] = {}

        response = await handle_get_area_logs(mock_hass, "living_room", mock_request)

        assert response.status == 200
        import json

        body = json.loads(response.body.decode())

        # Should return empty logs list
        assert body["logs"] == []

    @pytest.mark.asyncio
    async def test_handle_get_area_logs_error(self, mock_hass, mock_area_logger, mock_request):
        """Test getting area logs when error occurs."""
        # Make async_get_logs raise exception
        mock_area_logger.async_get_logs.side_effect = Exception("Database error")

        response = await handle_get_area_logs(mock_hass, "living_room", mock_request)

        assert response.status == 500
        import json

        body = json.loads(response.body.decode())

        assert "error" in body
        assert "Database error" in body["error"]

    @pytest.mark.asyncio
    async def test_handle_get_area_device_logs_no_manager(self, mock_hass):
        """Test device logs handler returns empty when no manager provided."""
        mock_request = MagicMock()
        mock_request.query = {}

        # Pass area_manager as None
        from smart_heating.api.handlers.logs import handle_get_area_device_logs

        response = await handle_get_area_device_logs(mock_hass, None, "living_room", mock_request)
        assert response.status == 200
        import json

        body = json.loads(response.body.decode())
        assert body["logs"] == []

    @pytest.mark.asyncio
    async def test_handle_get_area_device_logs_with_manager(self, mock_hass):
        """Test device logs handler returns logs and passes params through."""
        mock_request = MagicMock()
        mock_request.query = {
            "limit": "5",
            "since": "2025-01-01T00:00:00Z",
            "device_id": "d1",
            "direction": "sent",
        }

        # Mock manager
        manager = MagicMock()
        manager.async_get_device_logs = MagicMock(return_value=[{"device_id": "d1"}])

        from smart_heating.api.handlers.logs import handle_get_area_device_logs

        response = await handle_get_area_device_logs(
            mock_hass, manager, "living_room", mock_request
        )
        assert response.status == 200
        import json

        body = json.loads(response.body.decode())
        assert "logs" in body
        assert body["logs"][0]["device_id"] == "d1"
        manager.async_get_device_logs.assert_called_once_with(
            area_id="living_room",
            limit=5,
            since="2025-01-01T00:00:00Z",
            device_id="d1",
            direction="sent",
        )

    @pytest.mark.asyncio
    async def test_handle_get_area_device_logs_error(self, mock_hass):
        """Test device logs handler returns 500 on errors."""
        mock_request = MagicMock()
        mock_request.query = {}

        manager = MagicMock()
        manager.async_get_device_logs = MagicMock(side_effect=Exception("boom"))

        from smart_heating.api.handlers.logs import handle_get_area_device_logs

        response = await handle_get_area_device_logs(
            mock_hass, manager, "living_room", mock_request
        )
        assert response.status == 500
        import json

        body = json.loads(response.body.decode())
        assert "error" in body
        assert "boom" in body["error"]
