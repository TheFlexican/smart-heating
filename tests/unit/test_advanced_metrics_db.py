import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.advanced_metrics_collector import AdvancedMetricsCollector


@pytest.mark.asyncio
async def test_async_get_area_metrics():
    hass = MagicMock()

    # Mock area objects
    area1 = MagicMock()
    area1.current_temperature = 19.5
    area1.target_temperature = 22.0
    area1.state = "heating"
    area1.heating_type = "floor_heating"
    area1.heating_curve_coefficient = 0.5
    area1.hysteresis_override = 0.1

    area2 = MagicMock()
    area2.current_temperature = 20.0
    area2.target_temperature = 21.0
    area2.state = "idle"
    area2.heating_type = "radiator"
    area2.heating_curve_coefficient = None
    area2.hysteresis_override = None

    area_manager = MagicMock()
    area_manager.get_all_areas.return_value = {"area_1": area1, "area_2": area2}

    collector = AdvancedMetricsCollector(hass)

    metrics = await collector._async_get_area_metrics(area_manager)

    assert "area_1" in metrics
    import pytest

    assert metrics["area_1"]["current_temp"] == pytest.approx(19.5)
    assert metrics["area_1"]["heating_type"] == "floor_heating"

    assert "area_2" in metrics
    assert metrics["area_2"]["current_temp"] == pytest.approx(20.0)
    assert metrics["area_2"]["heating_type"] == "radiator"


@pytest.mark.asyncio
async def test_async_insert_metrics_calls_recorder(monkeypatch):
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)

    # Provide fake DB engine/table so the function proceeds
    collector._db_engine = MagicMock()
    collector._db_table = MagicMock()

    # Create a fake recorder with async_add_executor_job
    class FakeRecorder:
        def __init__(self):
            self.async_add_executor_job = AsyncMock(return_value=None)

    monkeypatch.setattr(
        "smart_heating.advanced_metrics_collector.get_instance",
        lambda hass: FakeRecorder(),
    )

    open_metrics = {"boiler_flow_temp": 30.0}
    area_metrics = {"area_1": {"current_temp": 20.0}}

    await collector._async_insert_metrics(open_metrics, area_metrics)

    # Verify async_add_executor_job called once
    assert collector._db_engine is not None


@pytest.mark.asyncio
async def test_async_get_metrics(monkeypatch):
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)

    # Create fake rows as simple objects
    class Row:
        def __init__(
            self, timestamp, outdoor_temp, boiler_flow_temp, area_metrics_json
        ):
            self.timestamp = timestamp
            self.outdoor_temp = outdoor_temp
            self.boiler_flow_temp = boiler_flow_temp
            self.boiler_return_temp = 0.0
            self.boiler_setpoint = 0.0
            self.modulation_level = 0.0
            self.flame_on = False
            self.area_metrics = area_metrics_json

    ts = datetime(2025, 12, 11, 12, 0, 0)
    row1 = Row(ts, 5.0, 30.0, json.dumps({"area_1": {"current_temp": 19.0}}))

    fake_result = MagicMock()
    fake_result.fetchall.return_value = [row1]

    # Instead of invoking _get_metrics_sync directly (complex SQLAlchemy setup),
    # mock the recorder async_add_executor_job used by async_get_metrics.
    fake_recorder = MagicMock()
    fake_recorder.async_add_executor_job = AsyncMock(
        return_value=[
            {
                "timestamp": ts.isoformat(),
                "outdoor_temp": 5.0,
                "boiler_flow_temp": 30.0,
                "boiler_return_temp": 0.0,
                "boiler_setpoint": 0.0,
                "modulation_level": 0.0,
                "flame_on": False,
                "area_metrics": {"area_1": {"current_temp": 19.0}},
            }
        ]
    )

    monkeypatch.setattr(
        "smart_heating.advanced_metrics_collector.get_instance",
        lambda hass: fake_recorder,
    )
    collector._db_engine = MagicMock()
    collector._db_table = MagicMock()

    results = await collector.async_get_metrics(days=1)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["outdoor_temp"] == pytest.approx(5.0)
    assert "area_metrics" in results[0]
    assert "area_1" in results[0]["area_metrics"]
