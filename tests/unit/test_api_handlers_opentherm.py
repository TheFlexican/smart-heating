import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.api_handlers.opentherm import handle_calibrate_opentherm
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_area_manager():
    manager = MagicMock()
    manager.opentherm_gateway_id = None
    manager.async_save = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_handle_calibrate_opentherm_no_gateway(mock_hass, mock_area_manager):
    response = await handle_calibrate_opentherm(mock_hass, mock_area_manager, None)
    assert response.status == 400
    body = json.loads(response.body.decode())
    assert "error" in body
