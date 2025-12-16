from unittest.mock import MagicMock

import pytest
from smart_heating.advanced_metrics_collector import AdvancedMetricsCollector


@pytest.mark.asyncio
async def test_async_init_database_mysql(monkeypatch):
    hass = MagicMock()

    class FakeRecorder:
        def __init__(self):
            self.db_url = "mysql://localhost/smart"
            self.engine = MagicMock()

    # Patch the function reference used by the collector module
    monkeypatch.setattr(
        "smart_heating.advanced_metrics_collector.get_instance",
        lambda hass: FakeRecorder(),
    )

    # Prevent real metadata create_all from running
    monkeypatch.setattr("sqlalchemy.schema.MetaData.create_all", lambda self, engine: None)

    collector = AdvancedMetricsCollector(hass)
    result = await collector._async_init_database()
    assert result is True


@pytest.mark.asyncio
async def test_async_init_database_sqlite(monkeypatch):
    hass = MagicMock()

    class FakeRecorder:
        def __init__(self):
            self.db_url = "sqlite:///:memory:"
            self.engine = MagicMock()

    monkeypatch.setattr(
        "homeassistant.components.recorder.get_instance", lambda hass: FakeRecorder()
    )

    collector = AdvancedMetricsCollector(hass)
    result = await collector._async_init_database()
    assert result is False


@pytest.mark.asyncio
async def test_get_opentherm_metrics(monkeypatch):
    hass = MagicMock()

    # Create states map
    def get_state(entity_id):
        mapping = {
            "weather.forecast_thuis": None,
            "sensor.opentherm_gateway_otgw_otgw_boiler_flow_water_temperature": MagicMock(
                state="27.0"
            ),
            "sensor.opentherm_gateway_otgw_otgw_return_water_temperature": MagicMock(state="26.0"),
            "sensor.opentherm_gateway_otgw_otgw_control_setpoint": MagicMock(state="50.0"),
            "sensor.opentherm_gateway_otgw_otgw_relative_modulation_level": MagicMock(state="45.0"),
            "binary_sensor.opentherm_gateway_flame": MagicMock(state="on"),
        }
        return mapping.get(entity_id)

    hass.states.get.side_effect = get_state

    collector = AdvancedMetricsCollector(hass)
    metrics = await collector._async_get_opentherm_metrics()

    import pytest

    assert metrics["boiler_flow_temp"] == pytest.approx(27.0)
    assert metrics["boiler_return_temp"] == pytest.approx(26.0)
    assert metrics["boiler_setpoint"] == pytest.approx(50.0)
    assert metrics["modulation_level"] == pytest.approx(45.0)
    assert metrics["flame_on"] is True
