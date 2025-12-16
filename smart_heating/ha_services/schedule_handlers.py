"""Schedule service handlers for Smart Heating."""

import logging
import uuid

from homeassistant.core import ServiceCall

from ..area_manager import AreaManager
from ..const import (
    ATTR_AREA_ID,
    ATTR_DAYS,
    ATTR_NIGHT_BOOST_ENABLED,
    ATTR_NIGHT_BOOST_END_TIME,
    ATTR_NIGHT_BOOST_OFFSET,
    ATTR_NIGHT_BOOST_START_TIME,
    ATTR_SCHEDULE_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
)
from ..coordinator import SmartHeatingCoordinator
from ..models import Schedule

_LOGGER = logging.getLogger(__name__)


async def async_handle_add_schedule(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the add_schedule service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    schedule_id = call.data[ATTR_SCHEDULE_ID]
    time_str = call.data[ATTR_TIME]
    temperature = call.data[ATTR_TEMPERATURE]
    days = call.data.get(ATTR_DAYS)

    _LOGGER.debug(
        "Adding schedule %s to area %s: %s @ %.1f°C",
        schedule_id,
        area_id,
        time_str,
        temperature,
    )

    try:
        area_manager.add_schedule_to_area(area_id, schedule_id, time_str, temperature, days)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Added schedule %s to area %s", schedule_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to add schedule: %s", err)
