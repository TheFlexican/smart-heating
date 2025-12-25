import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.features.advanced_metrics_collector import AdvancedMetricsCollector


@pytest.mark.asyncio
async def test_async_init_database_supported(monkeypatch):
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)

    # Fake recorder with mysql db_url and engine with create_all
    class FakeRecorder:
        def __init__(self):
            self.db_url = "mysql://user:pass@host/db"
            self.engine = MagicMock()

    monkeypatch.setattr(
        "smart_heating.features.advanced_metrics_collector.get_instance",
        lambda hass: FakeRecorder(),
    )

    ok = await collector._async_init_database()
    assert ok is True
    assert collector._db_table is not None


@pytest.mark.asyncio
async def test_async_setup_success(monkeypatch):
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)

    # Make init database return True
    collector._async_init_database = AsyncMock(return_value=True)
    # Patch async_track_time_interval to return a dummy unsub function
    monkeypatch.setattr(
        "smart_heating.features.advanced_metrics_collector.async_track_time_interval",
        lambda hass, func, interval: (lambda: None),
    )

    collector._async_collect_metrics = AsyncMock(return_value=None)

    ok = await collector.async_setup()
    assert ok is True
    assert collector._initialized is True
    assert callable(collector._collection_unsub)
    assert callable(collector._cleanup_unsub)


@pytest.mark.asyncio
async def test_async_get_opentherm_metrics_various():
    # Use a simple MagicMock hass to allow state mocking
    hass = MagicMock()
    hass.states.get = MagicMock()

    # Weather entity returns temperature attribute
    weather = MagicMock()
    weather.attributes = {"temperature": 8}

    # One sensor returns numeric string, another unknown
    s1 = MagicMock()
    s1.state = "30.5"

    s2 = MagicMock()
    s2.state = "unknown"

    flame = MagicMock()
    flame.state = "on"

    def get_state(entity_id):
        if entity_id == "weather.forecast_thuis":
            return weather
        if "boiler_flow_water_temperature" in entity_id:
            return s1
        if "relative_modulation_level" in entity_id:
            return s2
        if "flame" in entity_id:
            return flame
        return None

    hass.states.get.side_effect = get_state

    collector = AdvancedMetricsCollector(hass)

    metrics = await collector._async_get_opentherm_metrics()
    assert metrics.get("outdoor_temp") == 8
    assert "boiler_flow_temp" in metrics
    assert metrics.get("flame_on") is True


def test_get_metrics_sync_area_filter_and_invalid_json():
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)

    # Create fake rows
    class Row:
        def __init__(self, timestamp, outdoor_temp, boiler_flow_temp, area_metrics_json):
            self.timestamp = timestamp
            self.outdoor_temp = outdoor_temp
            self.boiler_flow_temp = boiler_flow_temp
            self.boiler_return_temp = 0.0
            self.boiler_setpoint = 0.0
            self.modulation_level = 0.0
            self.flame_on = False
            self.area_metrics = area_metrics_json

    ts = datetime(2025, 12, 12, 12, 0, 0)
    row_good = Row(ts, 5.0, 30.0, json.dumps({"area_1": {"current_temp": 19.0}}))
    row_bad = Row(ts, 5.0, 30.0, "{not-json}")

    fake_result = MagicMock()
    fake_result.fetchall.return_value = [row_good, row_bad]

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, stmt):
            return fake_result

    fake_engine = MagicMock()
    fake_engine.connect.return_value.__enter__.return_value = FakeConn()

    # Patch select to be tolerant for test (returns object with where method)
    class DummySelect:
        def where(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return "stmt"

    import smart_heating.features.advanced_metrics_collector as amc

    amc.select = lambda tbl: DummySelect()

    collector._db_engine = fake_engine

    # Provide a dummy c.timestamp that supports comparison ops used in the query
    class DummyTimestamp:
        def __ge__(self, other):
            return True

        def __lt__(self, other):
            return False

    class DummyC:
        timestamp = DummyTimestamp()

    collector._db_table = MagicMock()
    collector._db_table.c = DummyC()

    results = collector._get_metrics_sync(ts, "area_1")
    assert isinstance(results, list)
    assert len(results) == 2
    assert "area_metrics" in results[0]
    assert results[0]["area_metrics"] == {"area_1": {"current_temp": 19.0}}
    assert results[1]["area_metrics"] == {}


def test_cleanup_old_metrics_sync():
    hass = MagicMock()
    collector = AdvancedMetricsCollector(hass)

    class Result:
        def __init__(self, count):
            self.rowcount = count

    class FakeBegin:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, stmt):
            return Result(7)

    fake_engine = MagicMock()
    fake_engine.begin.return_value.__enter__.return_value = FakeBegin()

    # Patch delete to return an object with where() that returns a dummy
    class DummyDelete:
        def where(self, *args, **kwargs):
            return "stmt"

    import smart_heating.features.advanced_metrics_collector as amc

    amc.delete = lambda tbl: DummyDelete()

    collector._db_engine = fake_engine

    class DummyTimestamp:
        def __ge__(self, other):
            return True

        def __lt__(self, other):
            return False

    class DummyC:
        timestamp = DummyTimestamp()

    collector._db_table = MagicMock()
    collector._db_table.c = DummyC()

    deleted = collector._cleanup_old_metrics_sync(datetime.now())
    assert deleted == 7
