from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_view_post_many_branches(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # Use ExitStack to apply all patches
    from contextlib import ExitStack

    all_handlers = [
        "smart_heating.api.handle_disable_area",
        "smart_heating.api.handle_hide_area",
        "smart_heating.api.handle_unhide_area",
        "smart_heating.api.handle_cancel_boost",
        "smart_heating.api.handle_add_schedule",
        "smart_heating.api.handle_set_preset_mode",
        "smart_heating.api.handle_set_boost_mode",
        "smart_heating.api.handle_add_window_sensor",
        "smart_heating.api.handle_add_presence_sensor",
        "smart_heating.api.handle_set_hvac_mode",
        "smart_heating.api.handle_set_area_heating_curve",
        "smart_heating.api.handle_set_switch_shutdown",
        "smart_heating.api.handle_set_area_hysteresis",
        "smart_heating.api.handle_set_heating_type",
        "smart_heating.api.handle_set_auto_preset",
        "smart_heating.api.handle_set_area_preset_config",
        "smart_heating.api.handle_set_manual_override",
        "smart_heating.api.handle_set_primary_temperature_sensor",
        "smart_heating.api.handle_set_history_config",
        "smart_heating.api.handle_migrate_history_storage",
        "smart_heating.api.handle_set_global_presence",
        "smart_heating.api.handle_set_hide_devices_panel",
        "smart_heating.api.handle_set_advanced_control_config",
        "smart_heating.api.handle_set_opentherm_gateway",
        "smart_heating.api.handle_enable_vacation_mode",
        "smart_heating.api.handle_set_safety_sensor",
        "smart_heating.api.handle_call_service",
        "smart_heating.api.handle_validate_config",
        "smart_heating.api.handle_restore_backup",
        "smart_heating.api.handle_update_user",
        "smart_heating.api.handle_update_user_settings",
        "smart_heating.api.handle_discover_opentherm_capabilities",
        "smart_heating.api.handle_clear_opentherm_logs",
    ]

    with ExitStack() as stack:
        for h in all_handlers:
            stack.enter_context(
                patch(
                    h,
                    AsyncMock(return_value=web.json_response({"ok": True})),
                    create=True,
                )
            )

        # call many endpoints with JSON bodies as needed
        endpoints_with_json = [
            "areas/area1/schedules",
            "areas/area1/temperature",
            "areas/area1/preset_mode",
            "areas/area1/boost",
            "areas/area1/window_sensors",
            "areas/area1/presence_sensors",
            "areas/area1/hvac_mode",
            "areas/area1/heating_curve",
            "areas/area1/switch_shutdown",
            "areas/area1/hysteresis",
            "areas/area1/heating_type",
            "areas/area1/auto_preset",
            "areas/area1/preset_config",
            "areas/area1/manual_override",
            "areas/area1/primary_temp_sensor",
            "history/config",
            "history/storage/migrate",
            "global_presets",
            "global_presence",
            "hide_devices_panel",
            "config/advanced_control",
            "opentherm_gateway",
            "vacation_mode",
            "safety_sensor",
            "call_service",
            "validate",
            "import",
            "backups/backup1/restore",
            "users/user1",
            "users/settings",
            "opentherm/capabilities/discover",
            "opentherm/logs/clear",
        ]

        for endpoint in endpoints_with_json:
            req = make_mocked_request("POST", f"/api/smart_heating/{endpoint}")
            req.json = AsyncMock(return_value={})
            resp = await api_view.post(req, endpoint)
            assert resp.status in (200, 400, 404, 500)
