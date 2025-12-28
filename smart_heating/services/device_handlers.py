"""Device service handlers for Smart Heating."""

import logging

from homeassistant.core import ServiceCall
from homeassistant.exceptions import HomeAssistantError

from ..const import ATTR_AREA_ID, ATTR_DEVICE_ID, ATTR_DEVICE_TYPE, DOMAIN
from ..core.area_manager import AreaManager
from ..core.coordinator import SmartHeatingCoordinator
from ..exceptions import DeviceError, ValidationError

_LOGGER = logging.getLogger(__name__)


async def async_handle_add_device(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the add_device_to_area service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    device_id = call.data[ATTR_DEVICE_ID]
    device_type = call.data[ATTR_DEVICE_TYPE]

    _LOGGER.debug("Adding device %s (type: %s) to area %s", device_id, device_type, area_id)

    try:
        area_manager.add_device_to_area(area_id, device_id, device_type)

        # Discover device capabilities for climate devices
        if device_type == "thermostat":
            hass = coordinator.hass
            capability_detector = hass.data[DOMAIN].get("device_capability_detector")
            if capability_detector:
                try:
                    await capability_detector.discover_and_cache(device_id)
                    _LOGGER.info("Discovered capabilities for device %s", device_id)
                except (HomeAssistantError, DeviceError, ValidationError) as err:
                    _LOGGER.warning("Failed to discover capabilities for %s: %s", device_id, err)

        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Added device %s to area %s", device_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to add device: %s", err)


async def async_handle_remove_device(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the remove_device_from_area service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    device_id = call.data[ATTR_DEVICE_ID]

    _LOGGER.debug("Removing device %s from area %s", device_id, area_id)

    try:
        area_manager.remove_device_from_area(area_id, device_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Removed device %s from area %s", device_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to remove device: %s", err)
