from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.advanced_metrics_collector import AdvancedMetricsCollector


@pytest.mark.asyncio
async def test_async_cleanup_old_metrics(monkeypatch):
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)

    # Set up db table and engine
    collector._db_engine = MagicMock()
    collector._db_table = MagicMock()

    # Prepare a recorder where async_add_executor_job returns a positive deleted count
    fake_recorder = MagicMock()
    fake_recorder.async_add_executor_job = AsyncMock(return_value=3)

    monkeypatch.setattr(
        "smart_heating.advanced_metrics_collector.get_instance",
        lambda hass: fake_recorder,
    )

    await collector._async_cleanup_old_metrics(None)
    # If it doesn't raise, it's fine. Also validate that recorder was called
    fake_recorder.async_add_executor_job.assert_called_once()


@pytest.mark.asyncio
async def test_async_insert_metrics_error(monkeypatch):
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)
    # Setup to raise on recorder
    collector._db_engine = MagicMock()
    collector._db_table = MagicMock()

    class BadRecorder:
        async def async_add_executor_job(self, fn, arg):
            raise RuntimeError("DB insert failed")

    monkeypatch.setattr(
        "smart_heating.advanced_metrics_collector.get_instance",
        lambda hass: BadRecorder(),
    )

    # Should not raise an exception
    await collector._async_insert_metrics({"boiler_flow_temp": 30.0}, {"a": {}})
