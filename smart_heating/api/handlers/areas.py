"""Area API handlers for Smart Heating.

This module re-exports handlers from split modules for backward compatibility.
"""

# Re-export CRUD handlers
from .area_crud import (
    handle_get_area,
    handle_get_areas,
)

# Re-export settings handlers
from .area_settings import (
    handle_disable_area,
    handle_enable_area,
    handle_hide_area,
    handle_set_area_heating_curve,
    handle_set_area_hysteresis,
    handle_set_area_pid,
    handle_set_area_preset_config,
    handle_set_auto_preset,
    handle_set_heating_type,
    handle_set_manual_override,
    handle_set_primary_temperature_sensor,
    handle_set_switch_shutdown,
    handle_set_temperature,
    handle_unhide_area,
)

__all__ = [
    # CRUD
    "handle_get_areas",
    "handle_get_area",
    # Settings
    "handle_set_temperature",
    "handle_enable_area",
    "handle_disable_area",
    "handle_hide_area",
    "handle_unhide_area",
    "handle_set_switch_shutdown",
    "handle_set_area_hysteresis",
    "handle_set_auto_preset",
    "handle_set_heating_type",
    "handle_set_area_heating_curve",
    "handle_set_area_pid",
    "handle_set_area_preset_config",
    "handle_set_manual_override",
    "handle_set_primary_temperature_sensor",
]
