"""Area-specific response builders for API handlers."""

from typing import Any


def build_default_area_data(area_id: str, area_name: str) -> dict[str, Any]:
    """Build default data for an area without stored settings.

    Args:
        area_id: Area identifier
        area_name: Area name

    Returns:
        Default area data dictionary
    """
    return {
        "id": area_id,
        "name": area_name,
        "enabled": True,
        "hidden": False,
        "state": "idle",
        "target_temperature": 20.0,
        "current_temperature": None,
        "devices": [],
        "schedules": [],
        "manual_override": False,
    }
