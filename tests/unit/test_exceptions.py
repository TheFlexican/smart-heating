"""Test custom exceptions."""

import pytest

from smart_heating.exceptions import (
    AreaNotFoundError,
    ConfigurationError,
    DeviceError,
    SafetySensorError,
    ScheduleError,
    SmartHeatingError,
    StorageError,
    ValidationError,
)


def test_exception_hierarchy():
    """Test exception inheritance."""
    assert issubclass(ValidationError, SmartHeatingError)
    assert issubclass(DeviceError, SmartHeatingError)
    assert issubclass(AreaNotFoundError, SmartHeatingError)
    assert issubclass(StorageError, SmartHeatingError)
    assert issubclass(ConfigurationError, SmartHeatingError)
    assert issubclass(ScheduleError, SmartHeatingError)
    assert issubclass(SafetySensorError, SmartHeatingError)


def test_base_exception_is_exception():
    """Test SmartHeatingError is an Exception."""
    assert issubclass(SmartHeatingError, Exception)


def test_validation_error():
    """Test ValidationError can be raised and caught."""
    with pytest.raises(ValidationError, match="Invalid temperature"):
        raise ValidationError("Invalid temperature: 100°C")


def test_device_error():
    """Test DeviceError can be raised and caught."""
    with pytest.raises(DeviceError, match="Thermostat not responding"):
        raise DeviceError("Thermostat not responding")


def test_area_not_found_error():
    """Test AreaNotFoundError can be raised and caught."""
    with pytest.raises(AreaNotFoundError, match="Area area_123 not found"):
        raise AreaNotFoundError("Area area_123 not found")


def test_storage_error():
    """Test StorageError can be raised and caught."""
    with pytest.raises(StorageError, match="Failed to save configuration"):
        raise StorageError("Failed to save configuration")


def test_configuration_error():
    """Test ConfigurationError can be raised and caught."""
    with pytest.raises(ConfigurationError, match="Missing required field"):
        raise ConfigurationError("Missing required field: api_key")


def test_schedule_error():
    """Test ScheduleError can be raised and caught."""
    with pytest.raises(ScheduleError, match="Invalid time format"):
        raise ScheduleError("Invalid time format: 25:00")


def test_safety_sensor_error():
    """Test SafetySensorError can be raised and caught."""
    with pytest.raises(SafetySensorError, match="Safety sensor not found"):
        raise SafetySensorError("Safety sensor not found")


def test_catch_specific_exception():
    """Test catching specific exception type."""
    try:
        raise DeviceError("Thermostat not responding")
    except DeviceError as e:
        assert "Thermostat" in str(e)
    else:
        pytest.fail("DeviceError was not raised")


def test_catch_base_exception():
    """Test catching via base exception."""
    try:
        raise ValidationError("Test error")
    except SmartHeatingError:
        pass  # Should catch
    else:
        pytest.fail("SmartHeatingError did not catch ValidationError")


def test_exception_chaining():
    """Test exception chaining with 'from' keyword."""
    original_error = ValueError("Original error")

    try:
        try:
            raise original_error
        except ValueError as e:
            raise ValidationError("Validation failed") from e
    except ValidationError as e:
        assert e.__cause__ is original_error
        assert str(e) == "Validation failed"


def test_exception_with_no_message():
    """Test exceptions can be raised without a message."""
    with pytest.raises(SmartHeatingError):
        raise SmartHeatingError()


def test_multiple_exception_types():
    """Test handling multiple exception types."""
    errors = []

    for exc_class, msg in [
        (ValidationError, "validation"),
        (DeviceError, "device"),
        (StorageError, "storage"),
    ]:
        try:
            raise exc_class(msg)
        except SmartHeatingError as e:
            errors.append(str(e))

    assert errors == ["validation", "device", "storage"]


def test_exception_str_representation():
    """Test string representation of exceptions."""
    error = ValidationError("Temperature must be between 5 and 35°C")
    assert str(error) == "Temperature must be between 5 and 35°C"


def test_exception_repr():
    """Test repr of exceptions."""
    error = DeviceError("Device timeout")
    assert "DeviceError" in repr(error)


def test_catch_order_specific_before_base():
    """Test that specific exceptions are caught before base exception."""
    caught_exception = None

    try:
        raise ValidationError("specific error")
    except ValidationError as e:
        caught_exception = "ValidationError"
    except SmartHeatingError as e:
        caught_exception = "SmartHeatingError"

    assert caught_exception == "ValidationError"


def test_reraise_as_different_exception():
    """Test re-raising one exception as another."""
    try:
        try:
            raise DeviceError("Original device error")
        except DeviceError:
            raise StorageError("Failed to log device error")
    except StorageError as e:
        assert str(e) == "Failed to log device error"
