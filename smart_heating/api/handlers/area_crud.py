"""Area CRUD API handlers for Smart Heating."""

import asyncio

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from ...core.area_manager import AreaManager
from ...models import Area
from ...utils import (
    build_area_response,
    build_device_info,
    get_coordinator_devices,
)
from ..responses import build_default_area_data


async def handle_get_areas(hass: HomeAssistant, area_manager: AreaManager) -> web.Response:
    """Get all Home Assistant areas.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response with HA areas
    """
    # Minimal async operation to satisfy async requirement (awaited by callers)
    await asyncio.sleep(0)

    area_registry = ar.async_get(hass)
    areas_data = [
        _build_area_data_for_registry(hass, area_manager, area)
        for area in area_registry.areas.values()
    ]
    return web.json_response({"areas": areas_data})


def _build_area_data_for_registry(hass: HomeAssistant, area_manager: AreaManager, area) -> dict:
    """Build area data for a registry area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area: Home Assistant area registry entry

    Returns:
        Area data dictionary
    """
    area_id = area.id
    area_name = area.name
    stored_area = area_manager.get_area(area_id)

    if stored_area:
        return _build_stored_area_data(hass, stored_area, area_name, area_id)

    return build_default_area_data(area_id, area_name)


def _build_stored_area_data(
    hass: HomeAssistant, stored_area: Area, area_name: str, area_id: str
) -> dict:
    """Build data for a stored area with devices.

    Args:
        hass: Home Assistant instance
        stored_area: Stored area instance
        area_name: Home Assistant area name
        area_id: Area identifier

    Returns:
        Area data dictionary
    """
    devices_list = []
    coordinator_devices = get_coordinator_devices(hass, area_id) or {}

    for dev_id, dev_data in stored_area.devices.items():
        state = hass.states.get(dev_id)
        coord_device = coordinator_devices.get(dev_id)
        devices_list.append(build_device_info(dev_id, dev_data, state, coord_device))

    area_response = build_area_response(stored_area, devices_list)
    area_response["name"] = area_name
    return area_response


async def handle_get_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Get a specific area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier

    Returns:
        JSON response with area data
    """
    area = area_manager.get_area(area_id)

    if area is None:
        return web.json_response({"error": f"Zone {area_id} not found"}, status=404)

    # Build devices list
    devices_list = []
    for dev_id, dev_data in area.devices.items():
        state = hass.states.get(dev_id)
        devices_list.append(build_device_info(dev_id, dev_data, state))

    # Build area response using utility
    area_data = build_area_response(area, devices_list)

    # Use a small await to satisfy async checks; the handler remains non-blocking
    await asyncio.sleep(0)

    return web.json_response(area_data)
