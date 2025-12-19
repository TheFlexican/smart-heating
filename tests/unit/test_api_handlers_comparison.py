from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp.test_utils import make_mocked_request
from smart_heating.api.handlers.comparison import (
    handle_get_comparison,
    handle_get_custom_comparison,
)


@pytest.mark.asyncio
async def test_handle_get_comparison_single_area():
    hass = MagicMock()
    area_manager = MagicMock()
    comparison_engine = MagicMock()
    comparison_engine.compare_periods = AsyncMock(return_value={"a": 1})

    req = make_mocked_request(
        "GET", "/api/smart_heating/comparison?type=week&offset=2&area_id=area1"
    )
    resp = await handle_get_comparison(hass, area_manager, comparison_engine, req)
    assert resp.status == 200
    import json as _json

    data = _json.loads(resp.body.decode())
    assert "comparison" in data


@pytest.mark.asyncio
async def test_handle_get_comparison_all_areas():
    hass = MagicMock()
    area_manager = MagicMock()
    comparison_engine = MagicMock()
    comparison_engine.compare_all_areas = AsyncMock(return_value={"a": 2})

    req = make_mocked_request("GET", "/api/smart_heating/comparison?type=week&offset=1")
    resp = await handle_get_comparison(hass, area_manager, comparison_engine, req)
    assert resp.status == 200
    import json as _json

    data = _json.loads(resp.body.decode())
    assert "comparisons" in data


@pytest.mark.asyncio
async def test_handle_get_comparison_exception():
    hass = MagicMock()
    area_manager = MagicMock()
    comparison_engine = MagicMock()
    comparison_engine.compare_periods = AsyncMock(side_effect=RuntimeError("boom"))

    req = make_mocked_request(
        "GET", "/api/smart_heating/comparison?type=week&offset=2&area_id=area1"
    )
    resp = await handle_get_comparison(hass, area_manager, comparison_engine, req)
    assert resp.status == 500


@pytest.mark.asyncio
async def test_handle_get_custom_comparison_missing_params():
    hass = MagicMock()
    comparison_engine = MagicMock()

    req = make_mocked_request("POST", "/api/smart_heating/comparison/custom")
    req.json = AsyncMock(return_value={})
    resp = await handle_get_custom_comparison(hass, comparison_engine, req)
    assert resp.status == 400


@pytest.mark.asyncio
async def test_handle_get_custom_comparison_invalid_date(monkeypatch):
    hass = MagicMock()
    comparison_engine = MagicMock()

    req = make_mocked_request("POST", "/api/smart_heating/comparison/custom")
    req.json = AsyncMock(
        return_value={
            "area_id": "a1",
            "start_a": "bad",
            "end_a": "2025-12-01T00:00:00",
            "start_b": "2025-11-01T00:00:00",
            "end_b": "2025-11-07T00:00:00",
        }
    )

    # Make parse_datetime raise ValueError
    import smart_heating.api.handlers.comparison as comp

    def raise_bad(s):
        raise ValueError("bad date")

    monkeypatch.setattr(comp.dt_util, "parse_datetime", raise_bad)

    resp = await handle_get_custom_comparison(hass, comparison_engine, req)
    assert resp.status == 400


@pytest.mark.asyncio
async def test_handle_get_custom_comparison_success():
    hass = MagicMock()
    comparison_engine = MagicMock()
    comparison_engine.compare_custom_periods = AsyncMock(return_value={"ok": True})

    req = make_mocked_request("POST", "/api/smart_heating/comparison/custom")
    req.json = AsyncMock(
        return_value={
            "area_id": "a1",
            "start_a": "2025-12-01T00:00:00",
            "end_a": "2025-12-02T00:00:00",
            "start_b": "2025-11-01T00:00:00",
            "end_b": "2025-11-02T00:00:00",
        }
    )

    resp = await handle_get_custom_comparison(hass, comparison_engine, req)
    assert resp.status == 200
    import json as _json

    data = _json.loads(resp.body.decode())
    assert "comparison" in data
