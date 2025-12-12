from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request
from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_handler_raises_500_on_exception(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    with patch("smart_heating.api.handle_get_status", AsyncMock(side_effect=RuntimeError("boom"))):
        req = make_mocked_request("GET", "/api/smart_heating/status")
        resp = await api_view.get(req, "status")
        assert resp.status == 500
        assert "boom" in (resp.text or "")
