"""Unit tests for HeatingCycleHandler behavior with airco areas."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.climate_handlers.heating_cycle import HeatingCycleHandler
from smart_heating.models.area import Area


@pytest.mark.asyncio
async def test_airco_area_excluded_from_boiler_control():
    hass = MagicMock()
    area_manager = MagicMock()
    handler = HeatingCycleHandler(hass, area_manager)

    # Create area using airco
    area = Area("a1", "Air Room")
    area.heating_type = "airco"
    area.target_temperature = 21.0

    # Mock device handler and temp handler
    device_handler = MagicMock()
    device_handler.async_control_thermostats = AsyncMock()
    device_handler.async_control_switches = AsyncMock()
    device_handler.async_control_valves = AsyncMock()

    temp_handler = MagicMock()

    heating_areas, max_temp = await handler.async_handle_heating_required(
        "a1", area, 18.0, 21.0, device_handler, temp_handler
    )

    # Airco area should not be included in boiler heating_areas
    assert heating_areas == []
    assert max_temp == 21.0

    # Thermostat control should still be invoked, but switches/valves should not
    device_handler.async_control_thermostats.assert_awaited()
    device_handler.async_control_switches.assert_not_awaited()
    device_handler.async_control_valves.assert_not_awaited()


@pytest.mark.asyncio
async def test_airco_area_stop_does_not_control_valves_or_switches():
    hass = MagicMock()
    area_manager = MagicMock()
    handler = HeatingCycleHandler(hass, area_manager)

    area = Area("a1", "Air Room")
    area.heating_type = "airco"
    area.target_temperature = 21.0

    device_handler = MagicMock()
    device_handler.async_control_thermostats = AsyncMock()
    device_handler.async_control_switches = AsyncMock()
    device_handler.async_control_valves = AsyncMock()

    await handler.async_handle_heating_stop("a1", area, 21.0, 21.0, device_handler)

    device_handler.async_control_thermostats.assert_awaited()
    device_handler.async_control_switches.assert_not_awaited()
    device_handler.async_control_valves.assert_not_awaited()


@pytest.mark.asyncio
async def test_airco_area_cooling_triggers_thermostat_cool_only():
    hass = MagicMock()
    area_manager = MagicMock()
    handler = HeatingCycleHandler(hass, area_manager)

    # Create area using airco
    area = Area("a1", "Air Room")
    area.heating_type = "airco"
    area.target_temperature = 18.0

    device_handler = MagicMock()
    device_handler.async_control_thermostats = AsyncMock()
    device_handler.async_control_switches = AsyncMock()
    device_handler.async_control_valves = AsyncMock()

    temp_handler = MagicMock()

    cooling_areas, min_temp = await handler.async_handle_cooling_required(
        "a1", area, 23.0, 18.0, device_handler, temp_handler
    )

    # For airco area, thermostat should be controlled with hvac_mode='cool'
    device_handler.async_control_thermostats.assert_awaited()
    device_handler.async_control_switches.assert_not_awaited()
    device_handler.async_control_valves.assert_not_awaited()
    assert cooling_areas == [area]
    assert min_temp == 18.0
