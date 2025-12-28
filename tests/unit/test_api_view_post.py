from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api.server import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_view_post_endpoints(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    # Create admin user for authentication
    admin_user = MagicMock()
    admin_user.is_admin = True
    admin_user.id = "admin-test-user"

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # Patch handlers used in POST
    with (
        patch(
            "smart_heating.api.server.handle_enable_area",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_add_device",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_frost_protection",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_cleanup_history",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_global_presets",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_import_config",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_create_user",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
    ):
        # Areas enable (no body)
        req = make_mocked_request("POST", "/api/smart_heating/areas/area1/enable")
        req["hass_user"] = admin_user
        resp = await api_view.post(req, "areas/area1/enable")
        assert resp.status == 200

        # Add device to area (with JSON body)
        req = make_mocked_request("POST", "/api/smart_heating/areas/area1/devices")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={"id": "dev1"})
        resp = await api_view.post(req, "areas/area1/devices")
        assert resp.status == 200

        # Frost protection
        req = make_mocked_request("POST", "/api/smart_heating/frost_protection")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={"enabled": True})
        resp = await api_view.post(req, "frost_protection")
        assert resp.status == 200

        # History cleanup
        req = make_mocked_request("POST", "/api/smart_heating/history/cleanup")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={})
        resp = await api_view.post(req, "history/cleanup")
        assert resp.status == 200

        # Global presets
        req = make_mocked_request("POST", "/api/smart_heating/global_presets")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={})
        resp = await api_view.post(req, "global_presets")
        assert resp.status == 200

        # Import config
        req = make_mocked_request("POST", "/api/smart_heating/import")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={})
        resp = await api_view.post(req, "import")
        assert resp.status == 200

        # Create user (user manager handler)
        req = make_mocked_request("POST", "/api/smart_heating/users")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={"username": "test"})
        resp = await api_view.post(req, "users")
        assert resp.status == 200
