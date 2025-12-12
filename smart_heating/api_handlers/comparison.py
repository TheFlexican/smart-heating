"""Historical comparison API handlers."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..area_manager import AreaManager
from ..comparison_engine import ComparisonEngine

_LOGGER = logging.getLogger(__name__)


async def handle_get_comparison(
    _hass: HomeAssistant,
    area_manager: AreaManager,
    comparison_engine: ComparisonEngine,
    request: web.Request,
) -> web.Response:
    """Get historical comparison for areas.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        comparison_engine: Comparison engine instance
        request: HTTP request

    Returns:
        JSON response with comparison data
    """
    try:
        # Get query parameters
        comparison_type = request.query.get("type", "week")
        offset = int(request.query.get("offset", "1"))
        area_id = request.query.get("area_id")

        if area_id and area_id != "all":
            # Single area comparison
            comparison = await comparison_engine.compare_periods(
                area_id, comparison_type, offset
            )
            return web.json_response({"comparison": comparison})
        else:
            # All areas comparison
            comparisons = await comparison_engine.compare_all_areas(
                area_manager, comparison_type, offset
            )
            return web.json_response({"comparisons": comparisons})

    except Exception as e:
        _LOGGER.error("Error getting comparison: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_custom_comparison(
    _hass: HomeAssistant,
    comparison_engine: ComparisonEngine,
    request: web.Request,
) -> web.Response:
    """Get custom date range comparison.

    Args:
        hass: Home Assistant instance
        comparison_engine: Comparison engine instance
        request: HTTP request

    Returns:
        JSON response with comparison data
    """
    try:
        # Get POST data
        data = await request.json()
        area_id = data.get("area_id")
        start_a = data.get("start_a")
        end_a = data.get("end_a")
        start_b = data.get("start_b")
        end_b = data.get("end_b")

        if not all([area_id, start_a, end_a, start_b, end_b]):
            return web.json_response(
                {
                    "error": "Missing required parameters: area_id, start_a, end_a, start_b, end_b"
                },
                status=400,
            )

        # Parse dates
        try:
            start_a_dt = dt_util.parse_datetime(start_a)
            end_a_dt = dt_util.parse_datetime(end_a)
            start_b_dt = dt_util.parse_datetime(start_b)
            end_b_dt = dt_util.parse_datetime(end_b)
        except ValueError as e:
            return web.json_response({"error": f"Invalid date format: {e}"}, status=400)

        if not all([start_a_dt, end_a_dt, start_b_dt, end_b_dt]):
            return web.json_response(
                {"error": "Invalid date format. Use ISO format."}, status=400
            )

        # Get comparison
        comparison = await comparison_engine.compare_custom_periods(
            area_id, start_a_dt, end_a_dt, start_b_dt, end_b_dt
        )

        return web.json_response({"comparison": comparison})

    except Exception as e:
        _LOGGER.error("Error getting custom comparison: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)
