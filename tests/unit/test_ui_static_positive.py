from unittest.mock import patch

import pytest
from aiohttp.test_utils import make_mocked_request

from smart_heating.api import SmartHeatingStaticView, SmartHeatingUIView


@pytest.mark.asyncio
async def test_ui_view_positive(hass):
    # Provide a fake index.html content
    html = "<html><body>Smart Heating UI</body></html>"
    hass.config.path = lambda p: "."

    # Patch aiofiles.open to return a context manager with read() returning html
    import asyncio

    class FakeFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def read(self):
            await asyncio.sleep(0)
            return html

    def fake_open(path, mode="r", encoding=None):
        # Return an object that is an async context manager
        return FakeFile()

    with patch("smart_heating.api.aiofiles.open", fake_open):
        ui_view = SmartHeatingUIView(hass)
        req = make_mocked_request("GET", "/smart_heating_ui")
        resp = await ui_view.get(req)
        assert resp.status == 200
        assert "Smart Heating UI" in (resp.text or "")


@pytest.mark.asyncio
async def test_static_view_positive(tmp_path, hass):
    # Create a file in tmp_path to emulate frontend dist
    d = tmp_path / "frontend" / "dist"
    d.mkdir(parents=True, exist_ok=True)
    (d / "asset.js").write_text("console.log('ok')")

    hass.config.path = lambda p: str(d)

    static_view = SmartHeatingStaticView(hass)
    req = make_mocked_request("GET", "/smart_heating_static/asset.js")
    resp = await static_view.get(req, "asset.js")
    assert resp.status == 200
    assert resp.body is not None
