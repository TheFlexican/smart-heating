from types import SimpleNamespace

from smart_heating.api import websocket as ws
from smart_heating.const import DOMAIN


class FakeConnection:
    def __init__(self):
        self.sent = []
        self.subscriptions = {}

    def send_error(self, id_, code, message):
        self.sent.append(("error", id_, code, message))

    def send_result(self, id_, result=None):
        self.sent.append(("result", id_, result))

    def send_message(self, msg):
        self.sent.append(("message", msg))


def test_build_device_info_thermostat_and_sensor():
    hass = SimpleNamespace()
    # mock state lookup
    state = SimpleNamespace(
        state="23.5",
        attributes={
            "current_temperature": 23.5,
            "temperature": 21.0,
            "hvac_action": "heating",
            "friendly_name": "Thermo",
        },
    )
    hass.states = SimpleNamespace(get=lambda dev_id: state if dev_id == "thermo_1" else None)

    dev_data = {"type": "thermostat"}
    info = ws._build_device_info(hass, "thermo_1", dev_data)
    assert info["state"] == "23.5"
    assert info["current_temperature"] == 23.5
    assert info["target_temperature"] == 21.0
    assert info["friendly_name"] == "Thermo"

    # temperature_sensor
    state2 = SimpleNamespace(state="15.0", attributes={"temperature": 15.0})
    hass.states = SimpleNamespace(get=lambda dev_id: state2 if dev_id == "sensor_1" else None)
    dev_data2 = {"type": "temperature_sensor"}
    info2 = ws._build_device_info(hass, "sensor_1", dev_data2)
    assert info2["temperature"] == 15.0

    # missing state should show unavailable
    hass.states = SimpleNamespace(get=lambda dev_id: None)
    info3 = ws._build_device_info(hass, "missing", {"type": "thermostat"})
    assert info3["state"] == "unavailable"


def test_get_all_areas_data_and_find_coordinator_and_forward():
    # Create a fake area with minimal attributes
    class Area:
        def __init__(self, area_id):
            self.area_id = area_id
            self.name = "Area " + area_id
            self.enabled = True
            self.state = "idle"
            self.target_temperature = 20.0
            self.current_temperature = 19.0
            self.devices = {"d1": {"type": "thermostat"}}
            self.schedules = {}
            self.night_boost_enabled = False
            self.night_boost_offset = None
            self.night_boost_start_time = None
            self.night_boost_end_time = None
            self.smart_boost_enabled = False
            self.smart_boost_target_time = None
            self.weather_entity_id = None
            self.preset_mode = None
            self.away_temp = None
            self.eco_temp = None
            self.comfort_temp = None
            self.home_temp = None
            self.sleep_temp = None
            self.activity_temp = None
            self.boost_mode_active = False
            self.boost_temp = None
            self.boost_duration = None
            self.hvac_mode = None
            self.window_sensors = []
            self.presence_sensors = []

    area = Area("a1")

    # coordinator object
    coordinator = SimpleNamespace(
        data={"areas": {"a1": {"foo": "bar"}}}, async_add_listener=lambda cb: (lambda: None)
    )

    hass = SimpleNamespace()
    hass.data = {DOMAIN: {"coord1": coordinator, "history": "x"}}
    # provide minimal state lookup for device info
    hass.states = SimpleNamespace(
        get=lambda dev_id: SimpleNamespace(
            state="19.0",
            attributes={
                "current_temperature": 19.0,
                "temperature": 20.0,
                "hvac_action": "idle",
                "friendly_name": "D1",
            },
        )
        if dev_id == "d1"
        else None
    )

    conn = FakeConnection()
    msg = {"id": 42}
    # Test forward messages callback
    cb = ws._create_forward_messages_callback(coordinator, conn, msg)
    cb()
    # ensure a message was sent
    assert any(m[0] == "message" for m in conn.sent)

    # Test _get_all_areas_data
    fake_area_manager = SimpleNamespace(get_all_areas=lambda: {"a1": area})
    areas_data = ws._get_all_areas_data(fake_area_manager, hass)
    assert isinstance(areas_data, list)
    assert areas_data[0]["id"] == "a1"

    # Test find coordinator
    found = ws._find_coordinator(hass)
    assert found is coordinator
