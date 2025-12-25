from unittest.mock import MagicMock

from smart_heating.utils.device_registry import (
    DeviceRegistry,
    build_device_dict,
)


def make_hass():
    hass = MagicMock()
    # For simplicity we don't rely on hass helpers; DeviceRegistry attributes
    # will be patched in tests directly where necessary.
    return hass


def test_get_device_type_variants():
    hass = make_hass()
    dr = DeviceRegistry(hass)
    state = MagicMock()
    state.attributes = {"device_class": None, "unit_of_measurement": "°C"}
    ent = MagicMock()
    ent.domain = "climate"
    ent.entity_id = "climate.1"
    assert dr.get_device_type(ent, state) == ("thermostat", "climate")

    ent.domain = "sensor"
    state.attributes = {"device_class": "temperature", "unit_of_measurement": "°C"}
    assert dr.get_device_type(ent, state) == ("sensor", "temperature")

    ent.domain = "number"
    state.attributes = {}
    assert dr.get_device_type(ent, state) == ("number", "number")

    ent.domain = "unknown"
    assert dr.get_device_type(ent, state) is None


def test_get_ha_area_and_filtering_and_build():
    hass = make_hass()
    drh = DeviceRegistry(hass)

    # patch registries
    dev_entry = MagicMock()
    dev_entry.area_id = "area_1"
    dev_entry.id = "area_1"
    drh._device_registry = MagicMock()
    drh._device_registry.async_get.return_value = dev_entry

    area_entry = MagicMock()
    area_entry.id = "area_1"
    area_entry.name = "Living Room"
    drh._area_registry = MagicMock()
    drh._area_registry.async_get_area.return_value = area_entry

    ent = MagicMock()
    ent.device_id = "dev1"
    ent.entity_id = "sensor.temp1"
    ent.domain = "sensor"
    state = MagicMock()
    state.state = "20.0"
    state.attributes = {"friendly_name": "Temp Sensor", "temperature": 20.0}

    # get_ha_area uses entity.device_id to query device registry
    ent.device_id = "dev1"
    area = drh.get_ha_area(ent)
    assert area == ("area_1", "Living Room")

    # filtering by hidden area name in entity id
    assert drh.should_filter_device(
        "sensor.living_room_temp",
        "Living Room Sensor",
        "Living Room",
        [{"id": "hid", "name": "Living Room"}],
    )
    # not filtered
    assert not drh.should_filter_device(
        "sensor.outdoor_temp", "Outdoor", None, [{"id": "hid", "name": "Basement"}]
    )

    # build device dict
    dev = build_device_dict(ent, state, "sensor", "temperature", ("area_1", "Living Room"), ["a1"])
    assert dev["id"] == "sensor.temp1"
    assert dev["ha_area_name"] == "Living Room"
