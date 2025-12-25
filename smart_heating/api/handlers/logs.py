"""Logging API handlers for Smart Heating."""

import logging
import asyncio

from aiohttp import web
from homeassistant.core import HomeAssistant

from ...const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def handle_get_area_logs(hass: HomeAssistant, area_id: str, request) -> web.Response:
    """Get logs for a specific area.

    Args:
        hass: Home Assistant instance
        area_id: Area identifier
        request: Request object for query parameters

    Returns:
        JSON response with logs
    """
    try:
        # Get optional query parameters
        limit = request.query.get("limit")
        event_type = request.query.get("type")

        # Get area logger from hass data
        area_logger = hass.data[DOMAIN].get("area_logger")
        if not area_logger:
            return web.json_response({"logs": []})

        # Get logs (async)
        logs = await area_logger.async_get_logs(
            area_id=area_id, limit=int(limit) if limit else None, event_type=event_type
        )

        return web.json_response({"logs": logs})

    except Exception as err:
        _LOGGER.error("Error getting logs for area %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_get_area_device_logs(
    hass: HomeAssistant, area_manager: object, area_id: str, request
) -> web.Response:
    """Get device send/receive logs for a specific area.

    Query params:
    - limit: max number of events (default 100)
    - since: ISO timestamp to filter events after
    - device_id: optional entity id to filter
    - direction: "sent" or "received"
    """
    try:
        await asyncio.sleep(0)
        _ = hass
        limit = int(request.query.get("limit", "100"))
        since = request.query.get("since")
        device_id = request.query.get("device_id")
        direction = request.query.get("direction")

        # area_manager is passed in by the API view
        if not area_manager:
            return web.json_response({"logs": []})

        logs = area_manager.async_get_device_logs(
            area_id=area_id, limit=limit, since=since, device_id=device_id, direction=direction
        )

        return web.json_response({"logs": logs})

    except Exception as err:
        _LOGGER.error("Error getting device logs for area %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)
