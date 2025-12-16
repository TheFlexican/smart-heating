from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from smart_heating.coordinator import SmartHeatingCoordinator


@pytest.mark.asyncio
async def test_startup_grace_period_prevents_manual_override(
    hass: HomeAssistant, mock_config_entry, mock_area_manager
):
    coordinator = SmartHeatingCoordinator(hass, mock_config_entry, mock_area_manager)
    # Enable startup grace period
    coordinator._startup_grace_period = True

    mock_area = MagicMock()
    mock_area.name = "Test"
    mock_area.devices = {"climate.test": {}}
    mock_area.get_effective_target_temperature.return_value = 21.0
    mock_area.target_temperature = 21.0
    mock_area.manual_override = False

    coordinator.area_manager.get_all_areas.return_value = {"area_test": mock_area}
    coordinator.area_manager.async_save = AsyncMock()

    # Apply temperature change during grace - should be ignored
    await coordinator._apply_manual_temperature_change("climate.test", 23.0)

    import pytest

    assert mock_area.target_temperature == pytest.approx(21.0)
    assert mock_area.manual_override is False

    # Disable grace and apply again - should set manual override
    coordinator._startup_grace_period = False
    await coordinator._apply_manual_temperature_change("climate.test", 23.0)

    assert mock_area.target_temperature == pytest.approx(23.0)
    assert mock_area.manual_override is True
    coordinator.area_manager.async_save.assert_called_once()
