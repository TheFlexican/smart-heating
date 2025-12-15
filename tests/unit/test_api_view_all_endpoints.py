from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_api_view_many_endpoints(hass, mock_area_manager):
    # Prepare hass.data
    hass.data.setdefault(DOMAIN, {})
    eff_calc = MagicMock()
    eff_calc.calculate_area_efficiency = AsyncMock(
        return_value={
            "area_id": "area_1",
            "period": "week",
            "start_time": "2025-12-01",
            "end_time": "2025-12-08",
            "energy_score": 75.0,
            "heating_time_percentage": 40.0,
            "heating_cycles": 5,
            "average_temperature_delta": 1.2,
            "recommendations": [],
        }
    )
    hass.data[DOMAIN]["efficiency_calculator"] = eff_calc
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # Map of endpoint -> handler patch target path
    targets = {
        "status": "smart_heating.api.handle_get_status",
        "config": "smart_heating.api.handle_get_config",
        "areas": "smart_heating.api.handle_get_areas",
        "areas/area1/history": "smart_heating.api.handle_get_history",
        "areas/area1/learning": "smart_heating.api.handle_get_learning_stats",
        "areas/area1/logs": "smart_heating.api.handle_get_area_logs",
        "devices": "smart_heating.api.handle_get_devices",
        "devices/refresh": "smart_heating.api.handle_refresh_devices",
        "entities/binary_sensor": "smart_heating.api.handle_get_binary_sensor_entities",
        "entities/weather": "smart_heating.api.handle_get_weather_entities",
        "entity_state/climate.test": "smart_heating.api.handle_get_entity_state",
        "global_presets": "smart_heating.api.handle_get_global_presets",
        "global_presence": "smart_heating.api.handle_get_global_presence",
        "hysteresis": "smart_heating.api.handle_get_hysteresis",
        "vacation_mode": "smart_heating.api.handle_get_vacation_mode",
        "safety_sensor": "smart_heating.api.handle_get_safety_sensor",
        "config/advanced_control": "smart_heating.api.handle_get_config",
        "history/config": "smart_heating.api.handle_get_history_config",
        "history/storage/info": "smart_heating.api.handle_get_history_storage_info",
        "history/storage/database/stats": "smart_heating.api.handle_get_database_stats",
        "export": "smart_heating.api.handle_export_config",
        "backups": "smart_heating.api.handle_list_backups",
        "users": "smart_heating.api.handle_get_users",
        "users/user1": "smart_heating.api.handle_get_user",
        "users/presence": "smart_heating.api.handle_get_presence_state",
        "users/preferences": "smart_heating.api.handle_get_active_preferences",
        "efficiency/all_areas": "smart_heating.api.handle_get_efficiency_report",
        "efficiency/report/area_1": "smart_heating.api.handle_get_efficiency_report",
        "efficiency/history/area_1": "smart_heating.api.handle_get_area_efficiency_history",
        "comparison": "smart_heating.api.handle_get_comparison",
        "comparison/custom": "smart_heating.api.handle_get_custom_comparison",
        "opentherm/logs": "smart_heating.api.handle_get_opentherm_logs",
        "opentherm/capabilities": "smart_heating.api.handle_get_opentherm_capabilities",
    }

    # Use ExitStack to apply multiple patches safely
    from contextlib import ExitStack

    with ExitStack() as stack:
        for target in set(targets.values()):
            stack.enter_context(
                patch(target, AsyncMock(return_value=web.json_response({"ok": True})))
            )

        # Call each endpoint and assert OK
        for endpoint in targets:
            req = make_mocked_request("GET", f"/api/smart_heating/{endpoint}")
            resp = await api_view.get(req, endpoint)
            if resp.status != 200:
                # Gather diagnostic information for failing endpoint
                body = resp.text or ""
                pytest.fail(
                    f"Endpoint {endpoint} returned status {resp.status}, body: {body}"
                )
