"""Validation utilities for API request data."""

from typing import Any, Dict, Optional, Tuple


def validate_temperature(
    temp: Any, min_temp: float = 5.0, max_temp: float = 35.0
) -> tuple[bool, Optional[str]]:
    """Validate temperature value.

    Args:
        temp: Temperature value to validate
        min_temp: Minimum allowed temperature
        max_temp: Maximum allowed temperature

    Returns:
        Tuple of (is_valid, error_message)
    """
    if temp is None:
        return False, "Temperature is required"

    try:
        temp_float = float(temp)
    except (ValueError, TypeError):
        return False, "Temperature must be a number"

    if temp_float < min_temp or temp_float > max_temp:
        return False, f"Temperature must be between {min_temp}°C and {max_temp}°C"

    return True, None


def _validate_time_format(time_str: str) -> tuple[bool, Optional[str]]:
    """Validate time string in HH:MM format.

    Args:
        time_str: Time string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(time_str, str) or ":" not in time_str:
        return False, "time must be in HH:MM format"

    try:
        hours, minutes = time_str.split(":")
        hours_int = int(hours)
        minutes_int = int(minutes)

        if hours_int < 0 or hours_int > 23:
            return False, "hours must be between 0 and 23"
        if minutes_int < 0 or minutes_int > 59:
            return False, "minutes must be between 0 and 59"
    except (ValueError, AttributeError):
        return False, "invalid time format"

    return True, None


def _validate_days_list(days: Any) -> tuple[bool, Optional[str]]:
    """Validate days list.

    Args:
        days: List of days to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(days, list) or len(days) == 0:
        return False, "days must be a non-empty list"

    # Expect numeric day indices 0..6 (Monday=0)
    for day in days:
        if not isinstance(day, int):
            return (
                False,
                f"invalid day: {day}. Days must be integer indices 0 (Monday) - 6 (Sunday)",
            )
        if day < 0 or day > 6:
            return False, f"invalid day index: {day}. Must be between 0 and 6"

    return True, None


def validate_schedule_data(data: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate schedule entry data.

    Args:
        data: Schedule data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if "time" not in data:
        return False, "time is required"

    if "temperature" not in data:
        return False, "temperature is required"

    if "days" not in data:
        return False, "days is required"

    # Validate time format (HH:MM)
    is_valid, error_msg = _validate_time_format(data["time"])
    if not is_valid:
        return False, error_msg

    # Validate temperature
    is_valid, error_msg = validate_temperature(data["temperature"])
    if not is_valid:
        return False, error_msg

    # Validate days
    is_valid, error_msg = _validate_days_list(data["days"])
    if not is_valid:
        return False, error_msg

    return True, None


def validate_area_id(area_id: str) -> tuple[bool, Optional[str]]:
    """Validate area ID.

    Args:
        area_id: Area identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not area_id:
        return False, "area_id is required"

    if not isinstance(area_id, str):
        return False, "area_id must be a string"

    return True, None


def validate_entity_id(entity_id: str) -> tuple[bool, Optional[str]]:
    """Validate entity ID format.

    Args:
        entity_id: Entity identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not entity_id:
        return False, "entity_id is required"

    if not isinstance(entity_id, str):
        return False, "entity_id must be a string"

    if "." not in entity_id:
        return False, "entity_id must be in format domain.object_id"

    return True, None


def validate_float_range(
    value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> tuple[bool, Optional[str]]:
    """Safely convert value to float and validate range.

    Args:
        value: Value to validate and convert
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, "Value is required"

    try:
        float_value = float(value)
    except (ValueError, TypeError):
        return False, "Value must be a number"

    if min_value is not None and float_value < min_value:
        return False, f"Value must be at least {min_value}"

    if max_value is not None and float_value > max_value:
        return False, f"Value must be at most {max_value}"

    return True, None


def validate_integer_range(
    value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None
) -> tuple[bool, Optional[str]]:
    """Safely convert value to integer and validate range.

    Args:
        value: Value to validate and convert
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, "Value is required"

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, "Value must be an integer"

    if min_value is not None and int_value < min_value:
        return False, f"Value must be at least {min_value}"

    if max_value is not None and int_value > max_value:
        return False, f"Value must be at most {max_value}"

    return True, None


def validate_heating_type(heating_type: Any) -> tuple[bool, Optional[str]]:
    """Validate heating type enum.

    Args:
        heating_type: Heating type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not heating_type:
        return False, "heating_type is required"

    if not isinstance(heating_type, str):
        return False, "heating_type must be a string"

    valid_types = ["radiator", "floor_heating", "airco"]
    if heating_type not in valid_types:
        return False, f"heating_type must be one of: {', '.join(valid_types)}"

    return True, None


def validate_hvac_mode(hvac_mode: Any) -> tuple[bool, Optional[str]]:
    """Validate HVAC mode enum.

    Args:
        hvac_mode: HVAC mode to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hvac_mode:
        return False, "hvac_mode is required"

    if not isinstance(hvac_mode, str):
        return False, "hvac_mode must be a string"

    valid_modes = ["off", "heat", "cool", "auto"]
    if hvac_mode not in valid_modes:
        return False, f"hvac_mode must be one of: {', '.join(valid_modes)}"

    return True, None


def sanitize_string_input(value: Any, max_length: int = 255) -> tuple[bool, Optional[str]]:
    """Sanitize string input to prevent injection attacks.

    Args:
        value: String value to sanitize
        max_length: Maximum allowed length (default: 255)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, "Value is required"

    if not isinstance(value, str):
        return False, "Value must be a string"

    if len(value) > max_length:
        return False, f"Value must be at most {max_length} characters"

    # Check for common injection patterns
    suspicious_patterns = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "eval(",
        "expression(",
        "../",
        "..\\",
    ]

    value_lower = value.lower()
    for pattern in suspicious_patterns:
        if pattern in value_lower:
            return False, f"Value contains suspicious pattern: {pattern}"

    return True, None
