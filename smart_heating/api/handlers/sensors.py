"""Sensor API handlers for Smart Heating."""

import asyncio
import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ...core.area_manager import AreaManager
from ...exceptions import SmartHeatingError
from ...utils import get_coordinator

_LOGGER = logging.getLogger(__name__)

ERROR_INTERNAL = "Internal server error"
MSG_ENTITY_ID_REQUIRED = "entity_id required"
UNEXPECTED_ERROR = "Unexpected error"


async def handle_add_window_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Add window sensor to an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with configuration

    Returns:
        JSON response
    """
    entity_id = data.get("entity_id")
    if not entity_id:
        return web.json_response({"error": MSG_ENTITY_ID_REQUIRED}, status=400)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        # Extract configuration parameters
        action_when_open = data.get("action_when_open", "reduce_temperature")
        temp_drop = data.get("temp_drop")

        area.add_window_sensor(entity_id, action_when_open, temp_drop)
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ...utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True, "entity_id": entity_id})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)
    except (HomeAssistantError, SmartHeatingError, KeyError):
        _LOGGER.exception("Unexpected error adding window sensor for area %s", area_id)
        return web.json_response({"error": ERROR_INTERNAL, "message": UNEXPECTED_ERROR}, status=500)


async def handle_remove_window_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, entity_id: str
) -> web.Response:
    """Remove window sensor from an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        entity_id: Entity ID to remove

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.remove_window_sensor(entity_id)
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ...utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)
    except (HomeAssistantError, SmartHeatingError, KeyError):
        _LOGGER.exception("Unexpected error removing window sensor for area %s", area_id)
        return web.json_response({"error": ERROR_INTERNAL, "message": UNEXPECTED_ERROR}, status=500)


async def handle_add_presence_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Add presence sensor to an area.

    Presence sensors control preset mode switching:
    - When away: Switch to "away" preset
    - When home: Switch back to previous preset

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with entity_id

    Returns:
        JSON response
    """
    entity_id = data.get("entity_id")
    if not entity_id:
        return web.json_response({"error": MSG_ENTITY_ID_REQUIRED}, status=400)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.add_presence_sensor(entity_id)
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ...utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True, "entity_id": entity_id})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)
    except (HomeAssistantError, SmartHeatingError, KeyError):
        _LOGGER.exception("Unexpected error adding presence sensor for area %s", area_id)
        return web.json_response({"error": ERROR_INTERNAL, "message": UNEXPECTED_ERROR}, status=500)


async def handle_remove_presence_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, entity_id: str
) -> web.Response:
    """Remove presence sensor from an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        entity_id: Entity ID to remove

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.remove_presence_sensor(entity_id)
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            await coordinator.async_request_refresh()

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


# noqa: ASYNC109 - Web API handlers must be async per aiohttp convention
async def handle_get_binary_sensor_entities(hass: HomeAssistant) -> web.Response:
    # Minimal await to satisfy async checkers
    await asyncio.sleep(0)
    """Get all binary sensor entities from Home Assistant.

    Also includes person and device_tracker entities for presence detection.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with list of binary sensor entities
    """
    entities = []

    # Get binary sensors
    for entity_id in hass.states.async_entity_ids("binary_sensor"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": state.attributes.get("device_class"),
                    },
                }
            )

    # Get person entities (for presence detection)
    for entity_id in hass.states.async_entity_ids("person"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": "presence",  # Virtual device class for filtering
                    },
                }
            )

    # Get device_tracker entities (for presence detection)
    for entity_id in hass.states.async_entity_ids("device_tracker"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": "presence",  # Virtual device class for filtering
                    },
                }
            )

    return web.json_response({"entities": entities})


# noqa: ASYNC109 - Web API handlers must be async per aiohttp convention
async def handle_get_weather_entities(hass: HomeAssistant) -> web.Response:
    """Get all weather entities from Home Assistant.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with list of weather entities
    """
    await asyncio.sleep(0)  # Minimal async operation to satisfy async requirement
    entities = []

    # Get weather entities
    for entity_id in hass.states.async_entity_ids("weather"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                    },
                }
            )

    return web.json_response({"entities": entities})


async def handle_get_trv_candidates(hass: HomeAssistant) -> web.Response:
    # Minimal await to satisfy async checkers
    await asyncio.sleep(0)
    """Get all sensor and binary_sensor entities useful for TRV selection.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with list of candidate entities
    """
    entities = []

    # Sensors (numeric valve position candidates)
    for entity_id in hass.states.async_entity_ids("sensor"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "unit_of_measurement": state.attributes.get("unit_of_measurement"),
                    },
                }
            )

    # Binary sensors (open/closed candidates)
    for entity_id in hass.states.async_entity_ids("binary_sensor"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": state.attributes.get("device_class"),
                    },
                }
            )

    return web.json_response({"entities": entities})


async def handle_add_trv_entity(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Add a TRV entity to an area configuration.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with entity_id and optional role/name

    Returns:
        JSON response
    """
    entity_id = data.get("entity_id")
    if not entity_id:
        return web.json_response({"error": MSG_ENTITY_ID_REQUIRED}, status=400)

    role = data.get("role")
    name = data.get("name")

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.add_trv_entity(entity_id, role=role, name=name)
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ...utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True, "entity_id": entity_id})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)
    except (HomeAssistantError, SmartHeatingError, KeyError):
        _LOGGER.exception("Unexpected error adding TRV entity for area %s", area_id)
        return web.json_response({"error": ERROR_INTERNAL, "message": UNEXPECTED_ERROR}, status=500)


async def handle_remove_trv_entity(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, entity_id: str
) -> web.Response:
    """Remove a TRV entity from an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        entity_id: Entity ID to remove

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.remove_trv_entity(entity_id)
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ...utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)
    except (HomeAssistantError, SmartHeatingError, KeyError):
        _LOGGER.exception("Unexpected error removing TRV entity for area %s", area_id)
        return web.json_response({"error": ERROR_INTERNAL, "message": UNEXPECTED_ERROR}, status=500)
