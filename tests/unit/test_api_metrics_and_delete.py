from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from smart_heating.api import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.mark.asyncio
async def test_metrics_advanced_not_available(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    req = make_mocked_request("GET", "/api/smart_heating/metrics/advanced")
    resp = await api_view.get(req, "metrics/advanced")

    assert resp.status == 503


@pytest.mark.asyncio
async def test_metrics_advanced_invalid_days(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    # Inject advanced_metrics_collector but days invalid
    adv = MagicMock()
    adv.async_get_metrics = AsyncMock(return_value=[])  # won't be called
    hass.data[DOMAIN]["advanced_metrics_collector"] = adv

    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # invalid days -> 400
    req = make_mocked_request("GET", "/api/smart_heating/metrics/advanced?days=5")
    resp = await api_view.get(req, "metrics/advanced")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_metrics_advanced_valid(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    adv = MagicMock()
    adv.async_get_metrics = AsyncMock(return_value=[{"outdoor_temp": 5.0}])
    hass.data[DOMAIN]["advanced_metrics_collector"] = adv

    api_view = SmartHeatingAPIView(hass, mock_area_manager)
    req = make_mocked_request("GET", "/api/smart_heating/metrics/advanced?days=7")
    resp = await api_view.get(req, "metrics/advanced")
    assert resp.status == 200
    import json

    text = resp.text or "{}"
    data = json.loads(text)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_delete_vacation_and_safety_sensor(hass, mock_area_manager):
    hass.data.setdefault(DOMAIN, {})
    api_view = SmartHeatingAPIView(hass, mock_area_manager)

    # Patch handlers
    with (
        patch(
            "smart_heating.api.handle_disable_vacation_mode",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
        patch(
            "smart_heating.api.handle_remove_safety_sensor",
            AsyncMock(return_value=web.json_response({"ok": True})),
        ),
    ):
        # Delete vacation mode
        req = make_mocked_request("DELETE", "/api/smart_heating/vacation_mode")
        resp = await api_view.delete(req, "vacation_mode")
        assert resp.status == 200

        # Safety sensor missing sensor_id -> 400
        req = make_mocked_request("DELETE", "/api/smart_heating/safety_sensor")
        resp = await api_view.delete(req, "safety_sensor")
        assert resp.status == 400

        # Safety sensor with query param provided
        req = make_mocked_request("DELETE", "/api/smart_heating/safety_sensor?sensor_id=sensor_1")
        resp = await api_view.delete(req, "safety_sensor")
        assert resp.status == 200
