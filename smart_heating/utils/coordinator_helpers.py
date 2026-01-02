"""Coordinator data utilities for Smart Heating."""

import inspect
import logging
from typing import Any, Optional

from homeassistant.core import HomeAssistant

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_coordinator(hass: HomeAssistant) -> Optional[Any]:
    """Get the Smart Heating coordinator instance.

    Args:
        hass: Home Assistant instance

    Returns:
        Coordinator instance or None
    """
    for _key, value in hass.data.get(DOMAIN, {}).items():
        # Ensure value looks like a real coordinator: it must have a dict-like
        # data attribute and an async request refresh method. MagicMock
        # frequently exposes attributes dynamically, so ensure the types to
        # avoid false positives in tests.
        if (
            getattr(value, "data", None) is not None
            and isinstance(value.data, dict)
            and hasattr(value, "async_request_refresh")
        ):
            # Only return if async_request_refresh is callable
            if callable(value.async_request_refresh):
                return value
    return None


async def call_maybe_async(func: callable, /, *args, **kwargs) -> Any:
    """Call a function that may be sync or async and return the result.

    If the function returns an awaitable, await it and return the awaited
    result. This is a safe helper to call possibly-mocked async functions
    in tests where MagicMock may be used.
    """
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


def get_coordinator_devices(hass: HomeAssistant, area_id: str) -> dict[str, Any]:
    """Get coordinator device data for an area.

    Args:
        hass: Home Assistant instance
        area_id: Area identifier

    Returns:
        Dictionary mapping device_id -> device_data
    """
    coordinator = get_coordinator(hass)
    if not coordinator or not coordinator.data:
        return {}

    areas_data = coordinator.data.get("areas", {})
    area_data = areas_data.get(area_id, {})

    device_dict = {}
    for device in area_data.get("devices", []):
        device_dict[device["id"]] = device

    return device_dict


def safe_coordinator_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove learning_engine from coordinator data before returning to API.

    The learning_engine contains circular references and is too large for JSON.

    Args:
        data: Coordinator data dictionary

    Returns:
        Filtered data dictionary
    """
    return {k: v for k, v in data.items() if k != "learning_engine"}
