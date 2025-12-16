from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from smart_heating.advanced_metrics_collector import DOMAIN, AdvancedMetricsCollector


@pytest.mark.asyncio
async def test_collect_metrics_full_flow(monkeypatch):
    hass = MagicMock()
    # Provide an area_manager with some areas
    area_manager = MagicMock()
    area_manager.get_all_areas.return_value = {
        "a1": MagicMock(current_temperature=20.0, target_temperature=21.0, state="heating"),
        "a2": MagicMock(current_temperature=19.0, target_temperature=21.0, state="idle"),
    }

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["area_manager"] = area_manager

    collector = AdvancedMetricsCollector(hass)
    collector._initialized = True
    collector._db_table = MagicMock()
    collector._db_engine = MagicMock()

    # Patch opentherm and area metrics retrieval
    collector._async_get_opentherm_metrics = AsyncMock(return_value={"outdoor_temp": 5.0})
    collector._async_get_area_metrics = AsyncMock(return_value={"a1": {}})

    # Fake recorder
    fake_recorder = MagicMock()
    fake_recorder.async_add_executor_job = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "smart_heating.advanced_metrics_collector.get_instance",
        lambda hass: fake_recorder,
    )

    await collector._async_collect_metrics(None)

    # Ensure recorder insert called
    fake_recorder.async_add_executor_job.assert_called()


@pytest.mark.asyncio
async def test_async_get_metrics_wrapper(monkeypatch):
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)
    collector._db_table = MagicMock()
    collector._db_engine = MagicMock()

    # Fake get_metrics sync to return list
    fake_recorder = MagicMock()
    fake_recorder.async_add_executor_job = AsyncMock(
        return_value=[{"timestamp": datetime.now().isoformat()}]
    )
    monkeypatch.setattr(
        "smart_heating.advanced_metrics_collector.get_instance",
        lambda hass: fake_recorder,
    )

    results = await collector.async_get_metrics(days=7)
    assert isinstance(results, list)
