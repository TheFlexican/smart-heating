"""Device management functionality for Area model."""

import logging
from typing import Any

from ..const import (
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_SWITCH,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
)

_LOGGER = logging.getLogger(__name__)


class AreaDeviceManager:
    """Manages device operations for an Area."""

    def __init__(self, area: "Area") -> None:
        """Initialize device manager.

        Args:
            area: The parent Area instance
        """
        self.area = area

    def add_device(self, device_id: str, device_type: str, mqtt_topic: str | None = None) -> None:
        """Add a device to the area.

        Args:
            device_id: Entity ID of the device
            device_type: Type of device (thermostat, sensor, switch, etc.)
            mqtt_topic: Optional MQTT topic for the device
        """
        self.area.devices[device_id] = {
            "type": device_type,
            "mqtt_topic": mqtt_topic,
        }
        _LOGGER.info(
            "Added device %s (type: %s) to area %s",
            device_id,
            device_type,
            self.area.area_id,
        )

    def remove_device(self, device_id: str) -> None:
        """Remove a device from the area.

        Args:
            device_id: Entity ID of the device to remove
        """
        if device_id in self.area.devices:
            del self.area.devices[device_id]
            _LOGGER.info("Removed device %s from area %s", device_id, self.area.area_id)

    def get_temperature_sensors(self) -> list[str]:
        """Get all temperature sensors in this area.

        Returns:
            List of temperature sensor entity IDs
        """
        return [
            device_id
            for device_id, info in self.area.devices.items()
            if info["type"] == DEVICE_TYPE_TEMPERATURE_SENSOR
        ]

    def get_thermostats(self) -> list[str]:
        """Get all thermostats in this area.

        Returns climate entities (type="climate") and thermostat devices (type="thermostat").
        This includes TRVs and other climate-controlled heating devices.

        Returns:
            List of thermostat entity IDs
        """
        return [
            device_id
            for device_id, info in self.area.devices.items()
            if info["type"] in (DEVICE_TYPE_THERMOSTAT, "climate")
        ]

    def get_opentherm_gateways(self) -> list[str]:
        """Get all OpenTherm gateways in this area.

        Returns:
            List of OpenTherm gateway entity IDs
        """
        return [
            device_id
            for device_id, info in self.area.devices.items()
            if info["type"] == DEVICE_TYPE_OPENTHERM_GATEWAY
        ]

    def get_switches(self) -> list[str]:
        """Get all switches in this area.

        Returns:
            List of switch entity IDs
        """
        return [
            device_id
            for device_id, info in self.area.devices.items()
            if info["type"] == DEVICE_TYPE_SWITCH
        ]

    def get_valves(self) -> list[str]:
        """Get all valves in this area.

        Returns:
            List of valve entity IDs
        """
        return [
            device_id
            for device_id, info in self.area.devices.items()
            if info["type"] == DEVICE_TYPE_VALVE
        ]
