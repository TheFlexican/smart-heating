import pytest
import types
from unittest.mock import AsyncMock, Mock, patch

import smart_heating as sh_init


class DummyEntry:
    def __init__(self, entry_id: str, options: dict | None = None):
        self.entry_id = entry_id
        self.options = options or {}


@pytest.mark.asyncio
async def test_uninstall_deletes_when_keep_false():
    hass = types.SimpleNamespace()
    hass.bus = Mock()

    entry = DummyEntry("entry-1", options={})

    with patch.object(sh_init, "clear_all_persistent_data", new=AsyncMock()) as mock_clear:
        await sh_init.async_remove_entry(hass, entry)

        mock_clear.assert_awaited_once_with(hass)
        hass.bus.fire.assert_called_once_with(
            "smart_heating_uninstalled", {"entry_id": "entry-1", "deleted": True}
        )


@pytest.mark.asyncio
async def test_uninstall_keeps_when_option_true():
    hass = types.SimpleNamespace()
    hass.bus = Mock()

    entry = DummyEntry("entry-2", options={"keep_data_on_uninstall": True})

    with patch.object(sh_init, "clear_all_persistent_data", new=AsyncMock()) as mock_clear:
        await sh_init.async_remove_entry(hass, entry)

        mock_clear.assert_not_awaited()
        hass.bus.fire.assert_not_called()
