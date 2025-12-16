from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_view_post_endpoints(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # Patch handlers used in POST
    with (
        patch(
            "smart_heating.api.handle_enable_area",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_add_device",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_set_frost_protection",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_cleanup_history",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_set_global_presets",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_import_config",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_create_user",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
    ):
        # Areas enable (no body)
        req = make_mocked_request("POST", "/api/smart_heating/areas/area1/enable")
        resp = await api_view.post(req, "areas/area1/enable")
        assert resp.status == 200

        # Add device to area (with JSON body)
        req = make_mocked_request("POST", "/api/smart_heating/areas/area1/devices")
        req.json = AsyncMock(return_value={"id": "dev1"})
        resp = await api_view.post(req, "areas/area1/devices")
        assert resp.status == 200

        # Frost protection
        req = make_mocked_request("POST", "/api/smart_heating/frost_protection")
        req.json = AsyncMock(return_value={"enabled": True})
        resp = await api_view.post(req, "frost_protection")
        assert resp.status == 200

        # History cleanup
        req = make_mocked_request("POST", "/api/smart_heating/history/cleanup")
        req.json = AsyncMock(return_value={})
        resp = await api_view.post(req, "history/cleanup")
        assert resp.status == 200

        # Global presets
        req = make_mocked_request("POST", "/api/smart_heating/global_presets")
        req.json = AsyncMock(return_value={})
        resp = await api_view.post(req, "global_presets")
        assert resp.status == 200

        # Import config
        req = make_mocked_request("POST", "/api/smart_heating/import")
        req.json = AsyncMock(return_value={})
        resp = await api_view.post(req, "import")
        assert resp.status == 200

        # Create user (user manager handler)
        req = make_mocked_request("POST", "/api/smart_heating/users")
        req.json = AsyncMock(return_value={"username": "test"})
        resp = await api_view.post(req, "users")
        assert resp.status == 200
