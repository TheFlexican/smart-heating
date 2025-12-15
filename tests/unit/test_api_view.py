from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_view_get_various_endpoints(hass, mock_area_manager):
    # ensure hass has a domain data map
    # Prepare required data for hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["efficiency_calculator"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # Patch handlers to return simple json responses
    with (
        patch(
            "smart_heating.api.handle_get_status",
            AsyncMock(return_value=web.json_response({"status": "ok"})),
        ),
        patch(
            "smart_heating.api.handle_get_config",
            AsyncMock(return_value=web.json_response({"config": "ok"})),
        ),
        patch(
            "smart_heating.api.handle_get_areas",
            AsyncMock(return_value=web.json_response({"areas": []})),
        ),
        patch(
            "smart_heating.api.handle_get_devices",
            AsyncMock(return_value=web.json_response({"devices": []})),
        ),
        patch(
            "smart_heating.api.handle_get_entity_state",
            AsyncMock(return_value=web.json_response({"state": "on"})),
        ),
        patch(
            "smart_heating.api.handle_get_global_presets",
            AsyncMock(return_value=web.json_response({"presets": []})),
        ),
        patch(
            "smart_heating.api.handle_get_efficiency_report",
            AsyncMock(
                return_value=web.json_response(
                    {"summary_metrics": {"energy_score": 50}}
                )
            ),
        ),
    ):
        # status
        req = make_mocked_request("GET", "/api/smart_heating/status")
        resp = await api_view.get(req, "status")
        assert resp.status == 200

        # config
        req = make_mocked_request("GET", "/api/smart_heating/config")
        resp = await api_view.get(req, "config")
        assert resp.status == 200

        # areas
        req = make_mocked_request("GET", "/api/smart_heating/areas")
        resp = await api_view.get(req, "areas")
        assert resp.status == 200

        # devices
        req = make_mocked_request("GET", "/api/smart_heating/devices")
        resp = await api_view.get(req, "devices")
        assert resp.status == 200

        # entity_state
        req = make_mocked_request("GET", "/api/smart_heating/entity_state/climate.test")
        resp = await api_view.get(req, "entity_state/climate.test")
        assert resp.status == 200

        # global presets
        req = make_mocked_request("GET", "/api/smart_heating/global_presets")
        resp = await api_view.get(req, "global_presets")
        assert resp.status == 200

        # efficiency all_areas
        req = make_mocked_request("GET", "/api/smart_heating/efficiency/all_areas")
        resp = await api_view.get(req, "efficiency/all_areas")
        assert resp.status == 200


@pytest.mark.asyncio
async def test_api_view_unknown_endpoint(hass, mock_area_manager):
    api_view = SmartHeatingAPIView(hass, mock_area_manager)
    req = make_mocked_request("GET", "/api/smart_heating/undefined_endpoint")
    resp = await api_view.get(req, "undefined_endpoint")
    assert resp.status == 404
    # web.Response.text is a property; check for content directly
    text = resp.text or ""
    assert "Unknown endpoint" in text or "error" in text
