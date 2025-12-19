from unittest.mock import MagicMock

from smart_heating.utils.response_builders import build_area_response, build_device_info


def test_build_device_info_and_area_response():
    state = MagicMock()
    state.attributes = {
        "friendly_name": "Dev1",
        "temperature": 21.0,
        "current_temperature": 20.5,
    }
    state.state = "on"
    device_data = {"type": "sensor", "mqtt_topic": "topic"}
    coordinator_device = {
        "state": "on",
        "temperature": 21.0,
        "current_temperature": 20.5,
        "target_temperature": 22.0,
    }
    dev_inf = build_device_info("sensor.dev1", device_data, state, coordinator_device)
    assert dev_inf["id"] == "sensor.dev1"
    assert dev_inf["name"] == "Dev1"
    assert dev_inf["state"] == "on"

    area = MagicMock()
    area.area_id = "a1"
    area.name = "Area 1"
    area.enabled = True
    area.hidden = False
    area.state = "heating"
    area.target_temperature = 21.0
    area.get_effective_target_temperature.return_value = 20.5
    area.current_temperature = 20.5
    area.schedules = {}
    area.night_boost_enabled = False
    area.night_boost_offset = 0.5
    area.night_boost_start_time = None
    area.night_boost_end_time = None
    area.smart_boost_enabled = False
    area.smart_boost_target_time = None
    area.weather_entity_id = None
    area.preset_mode = "home"
    area.away_temp = 15.0
    area.eco_temp = 18.0
    area.comfort_temp = 21.0
    area.home_temp = 20.0
    area.sleep_temp = 17.0
    area.activity_temp = 22.0
    area.use_global_away = False
    area.use_global_eco = False
    area.use_global_comfort = False
    area.use_global_home = False
    area.use_global_sleep = False
    area.use_global_activity = False
    area.boost_mode_active = False
    area.boost_temp = 22.0
    area.boost_duration = 60
    area.hvac_mode = "heat"
    area.hysteresis_override = None
    area.manual_override = False
    area.window_sensors = []
    area.presence_sensors = []
    area.use_global_presence = False
    area.auto_preset_enabled = False
    area.auto_preset_home = "home"
    area.auto_preset_away = "away"
    area.shutdown_switches_when_idle = True
    area.shutdown_switch_entities = []
    area.primary_temperature_sensor = None
    area.heating_type = "radiator"
    area.custom_overhead_temp = None

    resp = build_area_response(area, [])
    assert resp["id"] == "a1"
    assert resp["name"] == "Area 1"
    assert resp["state"] == "heating"
