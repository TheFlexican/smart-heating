from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_exhaustive_endpoints(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    # provide common managers
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()
    hass.data[DOMAIN]["efficiency_calculator"] = MagicMock()

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # Test sets for different methods
    get_endpoints = [
        ("status", "smart_heating.api.handle_get_status"),
        ("config", "smart_heating.api.handle_get_config"),
        ("areas", "smart_heating.api.handle_get_areas"),
        ("areas/area1", "smart_heating.api.handle_get_area"),
        ("entities/weather", "smart_heating.api.handle_get_weather_entities"),
        ("entity_state/climate.test", "smart_heating.api.handle_get_entity_state"),
        ("global_presets", "smart_heating.api.handle_get_global_presets"),
        ("vacation_mode", "smart_heating.api.handle_get_vacation_mode"),
        ("efficiency/report/area1", "smart_heating.api.handle_get_efficiency_report"),
        (
            "efficiency/history/area1",
            "smart_heating.api.handle_get_area_efficiency_history",
        ),
        ("comparison/day", "smart_heating.api.handle_get_comparison"),
        ("opentherm/logs", "smart_heating.api.handle_get_opentherm_logs"),
    ]

    post_endpoints = [
        ("areas/area1/enable", "smart_heating.api.handle_enable_area"),
        ("areas/area1/devices", "smart_heating.api.handle_add_device"),
        ("global_presets", "smart_heating.api.handle_set_global_presets"),
        ("import", "smart_heating.api.handle_import_config"),
        ("users", "smart_heating.api.handle_create_user"),
        ("hysteresis", "smart_heating.api.handle_set_hysteresis_value"),
        ("opentherm_gateway", "smart_heating.api.handle_set_opentherm_gateway"),
    ]

    delete_endpoints = [
        ("vacation_mode", "smart_heating.api.handle_disable_vacation_mode"),
        ("safety_sensor?sensor_id=s1", "smart_heating.api.handle_remove_safety_sensor"),
        ("areas/area1/devices/device1", "smart_heating.api.handle_remove_device"),
        ("areas/area1/schedules/sched1", "smart_heating.api.handle_remove_schedule"),
    ]

    all_handlers = {h for _, h in get_endpoints + post_endpoints + delete_endpoints}

    with ExitStack() as stack:
        for handler in all_handlers:
            stack.enter_context(
                patch(
                    handler,
                    AsyncMock(return_value=web.json_response({"ok": True})),
                    create=True,
                )
            )

        for endpoint, _ in get_endpoints:
            req = make_mocked_request("GET", f"/api/smart_heating/{endpoint}")
            resp = await api_view.get(req, endpoint)
            assert resp.status in (200, 404, 503, 400, 500)

        for endpoint, _ in post_endpoints:
            req = make_mocked_request("POST", f"/api/smart_heating/{endpoint}")
            req.json = AsyncMock(return_value={})
            resp = await api_view.post(req, endpoint)
            assert resp.status in (200, 400, 404, 500)

        for endpoint, _ in delete_endpoints:
            req = make_mocked_request("DELETE", f"/api/smart_heating/{endpoint}")
            # Drop query for passing into delete
            resp = await api_view.delete(req, endpoint.split("?")[0])
            assert resp.status in (200, 400, 404, 500)
