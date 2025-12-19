from unittest.mock import MagicMock

import pytest
from smart_heating.features.advanced_metrics_collector import AdvancedMetricsCollector


@pytest.mark.asyncio
async def test_area_metrics_include_thermostat_failures(monkeypatch):
    hass = MagicMock()

    # Mock area with a thermostat
    area = MagicMock()
    area.area_id = "living_room"
    area.current_temperature = 20.0
    area.target_temperature = 21.0
    area.state = "idle"
    area.get_thermostats.return_value = ["climate.t1"]

    manager = MagicMock()
    manager.get_all_areas.return_value = {"living_room": area}

    # Mock climate controller with device_handler exposing failure state
    device_handler = MagicMock()
    device_handler.get_thermostat_failure_state.return_value = {
        "count": 2,
        "last_failure": 1234567890.0,
        "retry_seconds": 120,
    }

    climate_controller = MagicMock()
    climate_controller.device_handler = device_handler

    hass.data = {"smart_heating": {"climate_controller": climate_controller}}

    collector = AdvancedMetricsCollector(hass)

    # Call internal method
    metrics = await collector._async_get_area_metrics(manager)

    assert "living_room" in metrics
    lm = metrics["living_room"]
    assert "thermostat_failures" in lm
    assert "climate.t1" in lm["thermostat_failures"]
    assert lm["thermostat_failures"]["climate.t1"]["count"] == 2
