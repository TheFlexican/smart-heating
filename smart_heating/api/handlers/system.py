"""System API handlers for Smart Heating."""

import asyncio
import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ...core.area_manager import AreaManager
from ...exceptions import SmartHeatingError

_LOGGER = logging.getLogger(__name__)

ERROR_INTERNAL = "Internal server error"


async def handle_get_status(area_manager: AreaManager) -> web.Response:
    """Get system status.

    Args:
        area_manager: Area manager instance

    Returns:
        JSON response with status
    """
    areas = area_manager.get_all_areas()

    status = {
        "area_count": len(areas),
        "active_areas": sum(1 for z in areas.values() if z.enabled),
        "total_devices": sum(len(z.devices) for z in areas.values()),
    }

    # Yield once to satisfy async checks without blocking
    await asyncio.sleep(0)
    return web.json_response(status)


async def handle_get_entity_state(hass: HomeAssistant, entity_id: str) -> web.Response:
    """Get entity state from Home Assistant.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to fetch

    Returns:
        JSON response with entity state
    """
    state = hass.states.get(entity_id)

    if not state:
        return web.json_response({"error": f"Entity {entity_id} not found"}, status=404)

    attributes = dict(state.attributes) if getattr(state, "attributes", None) else {}
    last_changed = getattr(state, "last_changed", None)
    last_updated = getattr(state, "last_updated", None)

    # Yield once to satisfy async checks without blocking
    await asyncio.sleep(0)

    return web.json_response(
        {
            "state": state.state,
            "attributes": attributes,
            "last_changed": last_changed.isoformat() if last_changed else None,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }
    )


async def handle_call_service(hass: HomeAssistant, data: dict) -> web.Response:
    """Call a Home Assistant service.

    Args:
        hass: Home Assistant instance
        data: Service call data

    Returns:
        JSON response
    """
    service_name = data.get("service")
    if not service_name:
        return web.json_response({"error": "Service name required"}, status=400)

    try:
        service_data = {k: v for k, v in data.items() if k != "service"}

        await hass.services.async_call(
            "smart_heating",
            service_name,
            service_data,
            blocking=True,
        )

        return web.json_response(
            {"success": True, "message": f"Service {service_name} called successfully"}
        )
    except (HomeAssistantError, SmartHeatingError, OSError, RuntimeError) as err:
        _LOGGER.exception("Error calling service %s", service_name)
        # Keep 'error' containing the original exception message for backwards compatibility
        return web.json_response({"error": str(err), "message": ERROR_INTERNAL}, status=500)
