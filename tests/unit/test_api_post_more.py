from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api.server import (
    SmartHeatingAPIView,
    SmartHeatingStaticView,
    SmartHeatingUIView,
)
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_view_post_more_endpoints(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    # Create admin user for authentication
    admin_user = MagicMock()
    admin_user.is_admin = True
    admin_user.id = "admin-test-user"

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    with (
        patch(
            "smart_heating.api.server.handle_set_temperature",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_preset_mode",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_area_heating_curve",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_hysteresis_value",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_opentherm_gateway",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_advanced_control_config",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_switch_shutdown",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_heating_type",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_manual_override",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.server.handle_set_focus",
            AsyncMock(return_value=web.json_response({"ok": True})),
            create=True,
        ),
    ):
        # set temperature
        req = make_mocked_request("POST", "/api/smart_heating/areas/area1/temperature")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={"temperature": 23.0})
        resp = await api_view.post(req, "areas/area1/temperature")
        assert resp.status == 200

        # set preset mode
        req = make_mocked_request("POST", "/api/smart_heating/areas/area1/preset_mode")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={"preset_mode": "sleep"})
        resp = await api_view.post(req, "areas/area1/preset_mode")
        assert resp.status == 200

        # set heating curve
        req = make_mocked_request("POST", "/api/smart_heating/areas/area1/heating_curve")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={"coefficient": 1.1})
        resp = await api_view.post(req, "areas/area1/heating_curve")
        assert resp.status == 200

        # set hysteresis
        req = make_mocked_request("POST", "/api/smart_heating/hysteresis")
        req["hass_user"] = admin_user
        req.json = AsyncMock(return_value={"value": 0.5})
        hass.data[DOMAIN]["coordinator"] = MagicMock()  # some identifier
        resp = await api_view.post(req, "hysteresis")
        assert resp.status == 200


@pytest.mark.asyncio
async def test_ui_and_static_views(hass):
    ui_view = SmartHeatingUIView(hass)
    static_view = SmartHeatingStaticView(hass)

    # UI index path missing -> 500
    hass.config.path = lambda p: "/non/existing/path"
    req = make_mocked_request("GET", "/smart_heating_ui")
    resp = await ui_view.get(req)
    assert resp.status == 500

    # Static file not found -> 404
    req = make_mocked_request("GET", "/smart_heating_static/nonexistent.js")
    resp = await static_view.get(req, "nonexistent.js")
    assert resp.status == 404
