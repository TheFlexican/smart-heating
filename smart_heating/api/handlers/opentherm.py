"""OpenTherm logging API handlers for Smart Heating."""

import asyncio
import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ...const import DOMAIN
from ...exceptions import SmartHeatingError
from ...overshoot_protection import OvershootProtection

_LOGGER = logging.getLogger(__name__)


async def handle_get_opentherm_logs(hass: HomeAssistant, request) -> web.Response:  # NOSONAR
    """Get OpenTherm Gateway logs.

    Args:
        hass: Home Assistant instance
        request: Request object for query parameters

    Returns:
        JSON response with logs
    """
    try:
        await asyncio.sleep(0)
        # Get optional query parameters
        limit = request.query.get("limit")

        # Get OpenTherm logger from hass data
        opentherm_logger = hass.data[DOMAIN].get("opentherm_logger")
        if not opentherm_logger:
            return web.json_response({"logs": []})

        # Get logs
        logs = opentherm_logger.get_logs(limit=int(limit) if limit else None)

        return web.json_response({"logs": logs, "count": len(logs)})

    except (HomeAssistantError, ValidationError, KeyError, ValueError) as err:
        _LOGGER.error("Error getting OpenTherm logs: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_get_opentherm_capabilities(
    hass: HomeAssistant,
) -> web.Response:  # NOSONAR
    """Get OpenTherm Gateway capabilities.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with capabilities
    """
    try:
        await asyncio.sleep(0)
        opentherm_logger = hass.data[DOMAIN].get("opentherm_logger")
        if not opentherm_logger:
            return web.json_response({"capabilities": {}})

        capabilities = opentherm_logger.get_gateway_capabilities()

        return web.json_response(capabilities)

    except (HomeAssistantError, ValidationError, KeyError, ValueError) as err:
        _LOGGER.error("Error getting OpenTherm capabilities: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_get_opentherm_gateways(hass: HomeAssistant) -> web.Response:  # NOSONAR
    """Return a list of configured OpenTherm Gateway integration entries.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with list of gateways containing id and title
    """
    try:
        await asyncio.sleep(0)
        entries = hass.config_entries.async_entries("opentherm_gw")
        gateways = []
        for entry in entries:
            gw_id = (
                entry.data.get("id")
                or entry.data.get("gateway_id")
                or entry.options.get("id")
                or entry.options.get("gateway_id")
                or entry.entry_id
            )
            gateways.append({"gateway_id": gw_id, "title": entry.title})
        return web.json_response({"gateways": gateways})
    except (HomeAssistantError, ValidationError, KeyError, ValueError) as err:
        _LOGGER.error("Error listing OpenTherm gateways: %s", err)
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

    except (HomeAssistantError, ValidationError, KeyError, ValueError) as err:
        _LOGGER.error("Error discovering OpenTherm capabilities: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_clear_opentherm_logs(hass: HomeAssistant) -> web.Response:  # NOSONAR
    """Clear OpenTherm logs.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with success status
    """
    try:
        await asyncio.sleep(0)
        opentherm_logger = hass.data[DOMAIN].get("opentherm_logger")
        if not opentherm_logger:
            return web.json_response({"error": "OpenTherm logger not available"}, status=503)

        opentherm_logger.clear_logs()

        return web.json_response({"success": True, "message": "Logs cleared"})

    except (HomeAssistantError, ValidationError, KeyError, ValueError) as err:
        _LOGGER.error("Error clearing OpenTherm logs: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_calibrate_opentherm(
    hass: HomeAssistant,
    area_manager,
    coordinator,  # NOSONAR - hass needed for async context
) -> web.Response:
    """Calibrate the OpenTherm gateway overshoot protection value (OPV) and store it in AreaManager.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        coordinator: Coordinator with control functions

    Returns:
        JSON response containing OPV value or error
    """
    try:
        if not area_manager.opentherm_gateway_id:
            return web.json_response(
                {
                    "error": "No OpenTherm Gateway configured",
                    "details": "Please configure an OpenTherm gateway first.",
                },
                status=400,
            )

        # Check if coordinator supports modulation control
        if not hasattr(coordinator, "async_set_control_max_relative_modulation"):
            return web.json_response(
                {
                    "error": "Coordinator does not support modulation control",
                    "details": "Cannot run OPV calibration. The coordinator must support "
                    "async_set_control_max_relative_modulation method.",
                },
                status=503,
            )

        _LOGGER.info("Starting OPV calibration (approx. 2 minutes)")
        op = OvershootProtection(coordinator, "radiator")
        value = await op.calculate()
        if value is None:
            return web.json_response(
                {
                    "error": "Calibration failed to compute OPV value",
                    "details": "No boiler temperature samples could be read. "
                    "Check that the OpenTherm gateway is reporting flow temperature.",
                },
                status=500,
            )

        # Save to area manager
        area_manager.default_opv = value
        await area_manager.async_save()

        return web.json_response({"opv": value, "success": True})
    except (HomeAssistantError, SmartHeatingError, KeyError, ValueError) as err:
        _LOGGER.error("Error during OPV calibration: %s", err)
        return web.json_response({"error": "Calibration error", "details": str(err)}, status=500)
