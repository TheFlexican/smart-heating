"""Utility modules for Smart Heating."""
from .response_builders import build_area_response, build_device_info
from .validators import (
    validate_temperature,
    validate_schedule_data,
    validate_area_id,
    validate_entity_id,
)
from .device_registry import DeviceRegistry, build_device_dict
from .coordinator_helpers import (
    get_coordinator,
    get_coordinator_devices,
    safe_coordinator_data,
)

__all__ = [
    "build_area_response",
    "build_device_info",
    "validate_temperature",
    "validate_schedule_data",
    "validate_area_id",
    "validate_entity_id",
    "DeviceRegistry",
    "build_device_dict",
    "get_coordinator",
    "get_coordinator_devices",
    "safe_coordinator_data",
]
