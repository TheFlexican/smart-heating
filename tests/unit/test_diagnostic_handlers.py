from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.services.diagnostic_handlers import async_handle_force_thermostat_update


class MockState:
    def __init__(self, state, attributes=None):
        self._state = state
        self.attributes = attributes or {}

    @property
    def state(self):
        return self._state


@pytest.mark.asyncio
async def test_force_thermostat_update_with_switch_and_climate():
    hass = MagicMock()

    # initial state mapping
    state_map = {
        "switch.unit1_power": MockState("off"),
        "climate.unit1": MockState("off"),
    }

    def fake_get(entity_id):
        return state_map.get(entity_id)

    hass.states.get = MagicMock(side_effect=fake_get)

    async def fake_async_call(domain, service, data, blocking=False):
        # simulate switch.turn_on making the switch 'on'
        if domain == "switch" and service == "turn_on":
            entity_id = data.get("entity_id")
            state_map[entity_id] = MockState("on")
        return None

    hass.services.async_call = AsyncMock(side_effect=fake_async_call)

    # area manager with one area and one thermostat
    area = MagicMock()
    area.get_thermostats.return_value = ["climate.unit1"]
    area.devices = {"climate.unit1": {"type": "climate"}}

    area_manager = MagicMock()
    area_manager.get_area.return_value = area

    coordinator = MagicMock()
    coordinator.hass = hass

    call = SimpleNamespace()
    call.data = {"area_id": "a1", "temperature": 24.0, "hvac_mode": "heat"}

    await async_handle_force_thermostat_update(call, area_manager, coordinator)

    # Ensure we attempted to turn on the switch then call climate services
    assert hass.services.async_call.await_count >= 1
    # Verify the climate set_temperature was called (last call should be set_temperature)
    hass.services.async_call.assert_any_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.unit1", "temperature": 24.0},
        blocking=True,
    )


@pytest.mark.asyncio
async def test_force_thermostat_update_no_thermostats():
    hass = MagicMock()
    area = MagicMock()
    area.get_thermostats.return_value = []
    area_manager = MagicMock()
    area_manager.get_area.return_value = area
    coordinator = MagicMock()
    coordinator.hass = hass
    call = SimpleNamespace()
    call.data = {"area_id": "a1"}

    # Should complete without raising
    await async_handle_force_thermostat_update(call, area_manager, coordinator)
