"""Area API handlers for Smart Heating."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from ..area_manager import AreaManager
from ..const import DOMAIN
from ..models import Area
from ..utils import (
    build_area_response,
    build_device_info,
    get_coordinator,
    get_coordinator_devices,
)

_LOGGER = logging.getLogger(__name__)


def _set_heating_type(area: Area, area_id: str, heating_type: str) -> None:
    """Validate and apply heating type to an area.

    Raises ValueError on invalid input to allow the caller to return a 400 response.
    """
    if heating_type not in ["radiator", "floor_heating", "airco"]:
        raise ValueError("heating_type must be 'radiator', 'floor_heating' or 'airco'")

    area.heating_type = heating_type
    _LOGGER.info("Area %s: Setting heating_type to %s", area_id, heating_type)

    # If area is switched to air conditioning, clear/disable
    # settings that apply only to radiator/floor heating systems
    if heating_type == "airco":
        area.custom_overhead_temp = None
        area.heating_curve_coefficient = None
        area.hysteresis_override = None
        # Avoid shutting down switches by default for airco
        area.shutdown_switches_when_idle = False


def _apply_custom_overhead(area: Area, area_id: str, custom_overhead) -> None:
    """Validate and apply custom overhead temperature (or clear it)."""
    if custom_overhead is not None:
        # Validate range
        if custom_overhead < 0 or custom_overhead > 30:
            raise ValueError("custom_overhead_temp must be between 0 and 30°C")
        area.custom_overhead_temp = float(custom_overhead)
        _LOGGER.info("Area %s: Setting custom_overhead_temp to %.1f°C", area_id, custom_overhead)
    else:
        area.custom_overhead_temp = None
        _LOGGER.info("Area %s: Clearing custom_overhead_temp", area_id)

*** End Patch