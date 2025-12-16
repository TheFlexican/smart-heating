from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_opentherm_and_comparison_gets(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    with (
        patch(
            "smart_heating.api.handle_get_opentherm_gateways",
            AsyncMock(return_value=web.json_response({"gateways": []})),
        ),
        patch(
            "smart_heating.api.handle_calibrate_opentherm",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_get_comparison",
            AsyncMock(return_value=web.json_response({"comparison": []})),
        ),
        patch(
            "smart_heating.api.handle_get_custom_comparison",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
    ):
        # grapp OpenTherm gateways
        req = make_mocked_request("GET", "/api/smart_heating/opentherm/gateways")
        resp = await api_view.get(req, "opentherm/gateways")
        assert resp.status == 200

        # calibrate
        req = make_mocked_request("GET", "/api/smart_heating/opentherm/calibrate")
        resp = await api_view.get(req, "opentherm/calibrate")
        assert resp.status == 200

        # comparison
        req = make_mocked_request("GET", "/api/smart_heating/comparison")
        resp = await api_view.get(req, "comparison")
        assert resp.status == 200

        # custom comparison
        req = make_mocked_request("GET", "/api/smart_heating/comparison/custom")
        resp = await api_view.get(req, "comparison/custom")
        assert resp.status == 200
