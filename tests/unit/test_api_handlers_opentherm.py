import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.api_handlers.opentherm import handle_calibrate_opentherm
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_area_manager():
    manager = MagicMock()
    manager.opentherm_gateway_id = None
    manager.async_save = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_handle_calibrate_opentherm_no_gateway(mock_hass, mock_area_manager):
    response = await handle_calibrate_opentherm(mock_hass, mock_area_manager, None)
    assert response.status == 400
    body = json.loads(response.body.decode())
    assert "error" in body


@pytest.mark.asyncio
async def test_opentherm_handlers_more_paths():
    from smart_heating.api_handlers.opentherm import (
        handle_clear_opentherm_logs,
        handle_discover_opentherm_capabilities,
        handle_get_opentherm_capabilities,
        handle_get_opentherm_gateways,
        handle_get_opentherm_logs,
    )

    hass = MagicMock()
    hass.data = {DOMAIN: {}}

    # logs empty
    req = MagicMock()
    req.query = {}
    resp = await handle_get_opentherm_logs(hass, req)
    assert resp.status == 200

    # capabilities empty
    resp = await handle_get_opentherm_capabilities(hass)
    assert resp.status == 200

    # gateways
    class Entry:
        def __init__(self, entry_id, title, data=None, options=None):
            self.entry_id = entry_id
            self.title = title
            self.data = data or {}
            self.options = options or {}

    e1 = Entry("one", "GW1", data={"id": "gw1"})
    e2 = Entry("two", "GW2", options={"gateway_id": "gw2"})
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = lambda domain: [e1, e2]
    resp = await handle_get_opentherm_gateways(hass)
    assert resp.status == 200

    # discover capabilities errors
    area_manager = MagicMock()
    resp = await handle_discover_opentherm_capabilities(hass, area_manager)
    assert resp.status == 503

    # discover with gateway id but no logger
    hass.data = {DOMAIN: {"opentherm_logger": MagicMock()}}
    area_manager.opentherm_gateway_id = None
    resp = await handle_discover_opentherm_capabilities(hass, area_manager)
    assert resp.status == 400

    # clear logs error and success
    hass.data = {DOMAIN: {}}
    resp = await handle_clear_opentherm_logs(hass)
    assert resp.status == 503
    ot_logger = MagicMock()
    hass.data = {DOMAIN: {"opentherm_logger": ot_logger}}
    resp = await handle_clear_opentherm_logs(hass)
    assert resp.status == 200

    # discover capabilities success
    ot_logger = MagicMock()
    ot_logger.async_discover_mqtt_capabilities = AsyncMock(return_value={"cap": True})
    hass.data = {DOMAIN: {"opentherm_logger": ot_logger}}
    area_manager.opentherm_gateway_id = "gw1"
    resp = await handle_discover_opentherm_capabilities(hass, area_manager)
    assert resp.status == 200


@pytest.mark.asyncio
async def test_calibrate_opv_paths(monkeypatch):
    from smart_heating.api_handlers.opentherm import handle_calibrate_opentherm

    hass = MagicMock()
    area_manager = MagicMock()
    area_manager.opentherm_gateway_id = "g1"

    class OPFail:
        async def calculate(self):
            return None

    monkeypatch.setattr(
        "smart_heating.api_handlers.opentherm.OvershootProtection", lambda *a, **k: OPFail()
    )
    resp = await handle_calibrate_opentherm(hass, area_manager, None)
    assert resp.status == 500

    class OPSuccess:
        async def calculate(self):
            return 2.5

    monkeypatch.setattr(
        "smart_heating.api_handlers.opentherm.OvershootProtection", lambda *a, **k: OPSuccess()
    )
    area_manager.async_save = AsyncMock()
    resp = await handle_calibrate_opentherm(hass, area_manager, MagicMock())
    assert resp.status == 200
