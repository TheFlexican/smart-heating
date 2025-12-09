"""OpenTherm logging API handlers for Smart Heating."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def handle_get_opentherm_logs(hass: HomeAssistant, request) -> web.Response:
    """Get OpenTherm Gateway logs.

    Args:
        hass: Home Assistant instance
        request: Request object for query parameters

    Returns:
        JSON response with logs
    """
    try:
        # Get optional query parameters
        limit = request.query.get("limit")

        # Get OpenTherm logger from hass data
        opentherm_logger = hass.data[DOMAIN].get("opentherm_logger")
        if not opentherm_logger:
            return web.json_response({"logs": []})

        # Get logs
        logs = opentherm_logger.get_logs(limit=int(limit) if limit else None)

        return web.json_response({"logs": logs, "count": len(logs)})

    except Exception as err:
        _LOGGER.error("Error getting OpenTherm logs: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_get_opentherm_capabilities(hass: HomeAssistant) -> web.Response:
    """Get OpenTherm Gateway capabilities.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with capabilities
    """
    try:
        opentherm_logger = hass.data[DOMAIN].get("opentherm_logger")
        if not opentherm_logger:
            return web.json_response({"capabilities": {}})

        capabilities = opentherm_logger.get_gateway_capabilities()

        return web.json_response(capabilities)

    except Exception as err:
        _LOGGER.error("Error getting OpenTherm capabilities: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_discover_opentherm_capabilities(hass: HomeAssistant, area_manager) -> web.Response:
    """Discover OpenTherm Gateway capabilities via MQTT.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response with discovered capabilities
    """
    try:
        opentherm_logger = hass.data[DOMAIN].get("opentherm_logger")
        if not opentherm_logger:
            return web.json_response({"error": "OpenTherm logger not available"}, status=503)

        gateway_id = area_manager.opentherm_gateway_id
        if not gateway_id:
            return web.json_response({"error": "No OpenTherm Gateway configured"}, status=400)

        capabilities = await opentherm_logger.async_discover_mqtt_capabilities(gateway_id)

        return web.json_response(capabilities)

    except Exception as err:
        _LOGGER.error("Error discovering OpenTherm capabilities: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_clear_opentherm_logs(hass: HomeAssistant) -> web.Response:
    """Clear OpenTherm logs.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with success status
    """
    try:
        opentherm_logger = hass.data[DOMAIN].get("opentherm_logger")
        if not opentherm_logger:
            return web.json_response({"error": "OpenTherm logger not available"}, status=503)

        opentherm_logger.clear_logs()

        return web.json_response({"success": True, "message": "Logs cleared"})

    except Exception as err:
        _LOGGER.error("Error clearing OpenTherm logs: %s", err)
        return web.json_response({"error": str(err)}, status=500)
