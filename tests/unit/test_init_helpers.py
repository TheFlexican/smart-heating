from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.__init__ import async_register_panel, async_setup_services


@pytest.mark.asyncio
async def test_async_register_panel_remove_raises(monkeypatch):
    hass = MagicMock()

    # Simulate async_remove_panel raising KeyError
    def raise_key(h, p):
        raise KeyError()

    monkeypatch.setattr("homeassistant.components.frontend.async_remove_panel", raise_key)
    called = {}

    def fake_register(*args, **kwargs):
        called["ok"] = True

    monkeypatch.setattr(
        "homeassistant.components.frontend.async_register_built_in_panel", fake_register
    )

    await async_register_panel(hass, MagicMock())
    assert called.get("ok") is True


@pytest.mark.asyncio
async def test_async_setup_services_registers_many():
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_register = MagicMock()

    coordinator = MagicMock()
    coordinator.area_manager = MagicMock()

    # Call the function synchronously (it is async but only registers services)
    await async_setup_services(hass, coordinator)

    # Expect multiple service registrations
    assert hass.services.async_register.call_count > 5


@pytest.mark.asyncio
async def test_climate_controller_heating_paths(monkeypatch):
    from smart_heating.climate.climate_controller import ClimateController

    hass = MagicMock()
    area_manager = MagicMock()

    # Build several fake areas to hit many branches
    def make_area(**kwargs):
        a = MagicMock()
        for k, v in kwargs.items():
            setattr(a, k, v)
        # default methods
        a.get_temperature_sensors.return_value = ["s1"]
        a.get_thermostats.return_value = ["t1"]
        a.get_effective_target_temperature.return_value = getattr(a, "target_temperature", 21.0)
        return a

    areas = {
        "disabled": make_area(enabled=False, current_temperature=20.0, target_temperature=22.0),
        "manual": make_area(
            enabled=True,
            manual_override=True,
            current_temperature=20.0,
            target_temperature=22.0,
        ),
        "offmode": make_area(
            enabled=True,
            hvac_mode="off",
            current_temperature=20.0,
            target_temperature=22.0,
        ),
        "notemp": make_area(enabled=True, current_temperature=None, target_temperature=22.0),
        "within_hyst": make_area(enabled=True, current_temperature=21.3, target_temperature=21.5),
        "heating": make_area(enabled=True, current_temperature=18.0, target_temperature=21.0),
        "cooling": make_area(
            enabled=True,
            current_temperature=25.0,
            target_temperature=21.0,
            hvac_mode="cool",
        ),
    }

    area_manager.get_all_areas.return_value = areas

    controller = ClimateController(hass, area_manager)

    # Replace handlers with fakes
    fake_cycle = MagicMock()
    fake_history = MagicMock()
    fake_history.async_save = AsyncMock()
    fake_history.async_record_temperature = AsyncMock()
    fake_cycle.async_prepare_heating_cycle = AsyncMock(return_value=(True, fake_history))
    fake_cycle.async_handle_heating_required = AsyncMock(return_value=(["heating"], 22.0))
    fake_cycle.async_handle_cooling_required = AsyncMock(return_value=None)
    fake_cycle.async_handle_heating_stop = AsyncMock(return_value=None)
    fake_cycle.async_handle_cooling_stop = AsyncMock(return_value=None)

    controller.cycle_handler = fake_cycle

    fake_prot = MagicMock()
    fake_prot.apply_vacation_mode = MagicMock()
    fake_prot.apply_frost_protection = MagicMock(side_effect=lambda aid, t: t)
    fake_prot.async_handle_disabled_area = AsyncMock()
    fake_prot.async_handle_manual_override = AsyncMock()
    controller.protection_handler = fake_prot

    # Device handler methods
    controller.device_handler.async_control_opentherm_gateway = AsyncMock()

    # Area logger to exercise logging
    controller.area_logger = MagicMock()

    await controller.async_control_heating()

    # Ensure cycle handler prepare called and opentherm gateway control called
    fake_cycle.async_prepare_heating_cycle.assert_called_once()
    controller.device_handler.async_control_opentherm_gateway.assert_called_once()
