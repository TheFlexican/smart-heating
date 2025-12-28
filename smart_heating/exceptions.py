"""Custom exceptions for Smart Heating integration."""


class SmartHeatingError(Exception):
    """Base exception for all Smart Heating errors."""

    pass


class ValidationError(SmartHeatingError):
    """Raised when input validation fails.

    Use for:
    - Invalid temperature values
    - Invalid entity IDs
    - Invalid configuration data
    - Malformed API requests
    """

    pass


class DeviceError(SmartHeatingError):
    """Raised when device communication fails.

    Use for:
    - Service call failures
    - Device timeout
    - Device not responding
    - HVAC mode change failures
    """

    pass


class AreaNotFoundError(SmartHeatingError):
    """Raised when an area cannot be found.

    Use for:
    - Invalid area_id in API calls
    - Deleted area referenced
    """

    pass


class StorageError(SmartHeatingError):
    """Raised when storage operations fail.

    Use for:
    - Failed to load configuration
    - Failed to save configuration
    - Corrupted storage data
    - Database connection errors
    """

    pass


class ConfigurationError(SmartHeatingError):
    """Raised when configuration is invalid.

    Use for:
    - Invalid integration configuration
    - Missing required config fields
    - Incompatible settings
    """

    pass


class ScheduleError(SmartHeatingError):
    """Raised when schedule operations fail.

    Use for:
    - Invalid schedule time format
    - Schedule conflict
    - Schedule not found
    """

    pass


class SafetySensorError(SmartHeatingError):
    """Raised when safety sensor issues occur.

    Use for:
    - Safety sensor not found
    - Safety alert active
    - Invalid safety sensor configuration
    """

    pass
