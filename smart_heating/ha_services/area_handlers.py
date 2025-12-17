"""Area service handlers for Smart Heating."""

import logging

from homeassistant.core import ServiceCall

from ..area_manager import AreaManager
from ..const import ATTR_AREA_ID, ATTR_TEMPERATURE, DOMAIN
from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_set_temperature(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_area_temperature service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    temperature = call.data[ATTR_TEMPERATURE]

    _LOGGER.debug("Setting area %s temperature to %.1f°C", area_id, temperature)

    try:
        area_manager.set_area_target_temperature(area_id, temperature)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Set area %s temperature to %.1f°C", area_id, temperature)
    except ValueError as err:
        _LOGGER.error("Failed to set temperature: %s", err)


async def async_handle_enable_area(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the enable_area service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]

    _LOGGER.debug("Enabling area %s", area_id)

    try:
        area_manager.enable_area(area_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        # Proactively update devices for immediate UX: set valves/thermostats to area target
        hass = coordinator.hass
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            area = area_manager.get_area(area_id)
            if area and area.current_temperature is not None:
                target = area.get_effective_target_temperature()
                # Check if heating is actually needed based on current vs target temp
                heating_needed = area.current_temperature < target
                _LOGGER.info(
                    "Area %s enabled: current=%.1f°C, target=%.1f°C, heating_needed=%s",
                    area_id,
                    area.current_temperature,
                    target,
                    heating_needed,
                )
                # Update thermostats and valves with appropriate heating state
                await climate_controller.device_handler.async_control_thermostats(
                    area, heating_needed, target
                )
                await climate_controller.device_handler.async_control_valves(
                    area, heating_needed, target
                )
        _LOGGER.info("Enabled area %s", area_id)
    except ValueError as err:
        _LOGGER.error("Failed to enable area: %s", err)


async def async_handle_disable_area(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the disable_area service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]

    _LOGGER.debug("Disabling area %s", area_id)

    try:
        area_manager.disable_area(area_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        # Proactively update devices for immediate UX: set valves to 'off' state
        hass = coordinator.hass
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            area = area_manager.get_area(area_id)
            if area:
                # Use explicit off for valves (0°C) to ensure TRVs close
                await climate_controller.device_handler.async_set_valves_to_off(area, 0.0)
                # Turn off thermostats (this may fall back to min setpoint)
                await climate_controller.device_handler.async_control_thermostats(area, False, None)
        _LOGGER.info("Disabled area %s", area_id)
    except ValueError as err:
        _LOGGER.error("Failed to disable area: %s", err)
