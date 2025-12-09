"""Efficiency report API handlers."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..efficiency_calculator import EfficiencyCalculator

_LOGGER = logging.getLogger(__name__)


async def handle_get_efficiency_report(
    hass: HomeAssistant,
    area_manager: AreaManager,
    efficiency_calculator: EfficiencyCalculator,
    request: web.Request,
) -> web.Response:
    """Get efficiency report for areas.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        efficiency_calculator: Efficiency calculator instance
        request: HTTP request

    Returns:
        JSON response with efficiency metrics
    """
    try:
        # Get query parameters
        period = request.query.get("period", "day")
        area_id = request.query.get("area_id")

        if area_id and area_id != "all":
            # Single area report
            metrics = await efficiency_calculator.calculate_area_efficiency(
                area_id, period
            )
            return web.json_response({"metrics": metrics})
        else:
            # All areas report
            metrics = await efficiency_calculator.calculate_all_areas_efficiency(
                area_manager, period
            )
            return web.json_response({"metrics": metrics})

    except Exception as e:
        _LOGGER.error("Error getting efficiency report: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_area_efficiency_history(
    hass: HomeAssistant,
    efficiency_calculator: EfficiencyCalculator,
    request: web.Request,
    area_id: str,
) -> web.Response:
    """Get efficiency history for a specific area over multiple periods.

    Args:
        hass: Home Assistant instance
        efficiency_calculator: Efficiency calculator instance
        request: HTTP request
        area_id: Area ID

    Returns:
        JSON response with historical efficiency data
    """
    try:
        # Get query parameters
        periods = int(request.query.get("periods", "7"))  # Default 7 days
        period_type = request.query.get("period_type", "day")

        history_data = []

        # Calculate efficiency for each period
        from datetime import timedelta
        from homeassistant.util import dt as dt_util

        end = dt_util.now()

        for i in range(periods):
            if period_type == "day":
                period_end = end - timedelta(days=i)
                period_start = period_end - timedelta(days=1)
            elif period_type == "week":
                period_end = end - timedelta(weeks=i)
                period_start = period_end - timedelta(weeks=1)
            elif period_type == "month":
                period_end = end - timedelta(days=30 * i)
                period_start = period_end - timedelta(days=30)
            else:
                period_end = end - timedelta(days=i)
                period_start = period_end - timedelta(days=1)

            metrics = await efficiency_calculator.calculate_area_efficiency(
                area_id, period_type, period_start, period_end
            )
            history_data.append(metrics)

        # Reverse to show oldest first
        history_data.reverse()

        return web.json_response({"history": history_data})

    except Exception as e:
        _LOGGER.error(
            "Error getting efficiency history for %s: %s", area_id, e, exc_info=True
        )
        return web.json_response({"error": str(e)}, status=500)
