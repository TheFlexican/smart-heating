"""Tests for validators utility functions."""

from smart_heating.utils.validators import (
    _validate_days_list,
    _validate_time_format,
    sanitize_string_input,
    validate_area_id,
    validate_entity_id,
    validate_float_range,
    validate_heating_type,
    validate_hvac_mode,
    validate_integer_range,
    validate_schedule_data,
    validate_temperature,
)


class TestValidateTemperature:
    """Tests for temperature validation."""

    def test_validate_temperature_valid(self):
        """Test validating valid temperature."""
        is_valid, error = validate_temperature(20.5)
        assert is_valid is True
        assert error is None

    def test_validate_temperature_none(self):
        """Test validating None temperature."""
        is_valid, error = validate_temperature(None)
        assert is_valid is False
        assert "required" in error

    def test_validate_temperature_too_low(self):
        """Test validating temperature too low."""
        is_valid, error = validate_temperature(0.0)
        assert is_valid is False
        assert "between" in error

    def test_validate_temperature_too_high(self):
        """Test validating temperature too high."""
        is_valid, error = validate_temperature(40.0)
        assert is_valid is False
        assert "between" in error

    def test_validate_temperature_not_number(self):
        """Test validating non-number temperature."""
        is_valid, error = validate_temperature("invalid")
        assert is_valid is False
        assert "number" in error

    def test_validate_temperature_edge_min(self):
        """Test validating minimum temperature."""
        is_valid, error = validate_temperature(5.0)
        assert is_valid is True
        assert error is None

    def test_validate_temperature_edge_max(self):
        """Test validating maximum temperature."""
        is_valid, error = validate_temperature(35.0)
        assert is_valid is True
        assert error is None


class TestValidateAreaId:
    """Tests for area ID validation."""

    def test_validate_area_id_valid(self):
        """Test validating valid area ID."""
        is_valid, error = validate_area_id("living_room")
        assert is_valid is True
        assert error is None

    def test_validate_area_id_empty(self):
        """Test validating empty area ID."""
        is_valid, error = validate_area_id("")
        assert is_valid is False
        assert "required" in error

    def test_validate_area_id_not_string(self):
        """Test validating non-string area ID."""
        is_valid, error = validate_area_id(123)
        assert is_valid is False
        assert "string" in error


class TestValidateTimeFormat:
    """Tests for time format validation."""

    def test_validate_time_format_valid(self):
        """Test validating valid time."""
        is_valid, error = _validate_time_format("08:30")
        assert is_valid is True
        assert error is None

    def test_validate_time_format_no_colon(self):
        """Test validating time without colon."""
        is_valid, error = _validate_time_format("0830")
        assert is_valid is False
        assert "HH:MM" in error

    def test_validate_time_format_invalid_hour(self):
        """Test validating invalid hour."""
        is_valid, error = _validate_time_format("25:00")
        assert is_valid is False
        assert "hours" in error

    def test_validate_time_format_invalid_minute(self):
        """Test validating invalid minute."""
        is_valid, error = _validate_time_format("08:60")
        assert is_valid is False
        assert "minutes" in error

    def test_validate_time_format_edge_cases(self):
        """Test validating edge case times."""
        assert _validate_time_format("00:00")[0] is True
        assert _validate_time_format("23:59")[0] is True


class TestValidateDaysList:
    """Tests for days list validation."""

    def test_validate_days_list_valid(self):
        """Test validating valid days list."""
        is_valid, error = _validate_days_list([0, 1, 2])
        assert is_valid is True
        assert error is None

    def test_validate_days_list_empty(self):
        """Test validating empty days list."""
        is_valid, error = _validate_days_list([])
        assert is_valid is False
        assert "non-empty" in error

    def test_validate_days_list_not_list(self):
        """Test validating non-list."""
        is_valid, error = _validate_days_list("monday")
        assert is_valid is False
        assert "list" in error

    def test_validate_days_list_invalid_day(self):
        """Test validating invalid day."""
        is_valid, error = _validate_days_list([0, "invalid"])
        assert is_valid is False
        assert "invalid day" in error


class TestValidateScheduleData:
    """Tests for schedule data validation."""

    def test_validate_schedule_data_valid(self):
        """Test validating valid schedule data."""
        data = {"time": "08:00", "temperature": 21.0, "days": [0, 1, 2]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is True
        assert error is None

    def test_validate_schedule_data_missing_time(self):
        """Test validating schedule data without time."""
        data = {"temperature": 21.0, "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "time" in error

    def test_validate_schedule_data_missing_temperature(self):
        """Test validating schedule data without temperature."""
        data = {"time": "08:00", "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "temperature" in error

    def test_validate_schedule_data_missing_days(self):
        """Test validating schedule data without days."""
        data = {"time": "08:00", "temperature": 21.0}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "days" in error


class TestValidateEntityId:
    """Tests for entity ID validation."""

    def test_validate_entity_id_valid(self):
        """Test validating valid entity ID."""
        is_valid, error = validate_entity_id("climate.living_room")
        assert is_valid is True
        assert error is None

    def test_validate_entity_id_empty(self):
        """Test validating empty entity ID."""
        is_valid, error = validate_entity_id("")
        assert is_valid is False
        assert "required" in error

    def test_validate_entity_id_not_string(self):
        """Test validating non-string entity ID."""
        is_valid, error = validate_entity_id(123)
        assert is_valid is False
        assert "string" in error

    def test_validate_entity_id_no_domain(self):
        """Test validating entity ID without domain."""
        is_valid, error = validate_entity_id("livingroom")
        assert is_valid is False
        assert "domain.object_id" in error


class TestValidatorsEdgeCases:
    """Test edge cases in validators."""

    def test_validate_time_format_exception_handling(self):
        """Test time format validation with invalid types."""
        # This should trigger the except (ValueError, AttributeError) block
        is_valid, error = _validate_time_format(None)
        assert is_valid is False
        assert "HH:MM format" in error or "invalid time format" in error

    def test_validate_schedule_data_missing_time(self):
        """Test schedule validation missing time field."""
        data = {"temperature": 20.0, "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "time is required" in error

    def test_validate_schedule_data_missing_temperature(self):
        """Test schedule validation missing temperature field."""
        data = {"time": "08:00", "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "temperature is required" in error

    def test_validate_schedule_data_missing_days(self):
        """Test schedule validation missing days field."""
        data = {"time": "08:00", "temperature": 20.0}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "days is required" in error


class TestValidateFloatRange:
    """Tests for float range validation."""

    def test_validate_float_range_valid(self):
        """Test validating valid float."""
        is_valid, error = validate_float_range(10.5, min_value=0.0, max_value=100.0)
        assert is_valid is True
        assert error is None

    def test_validate_float_range_none(self):
        """Test validating None value."""
        is_valid, error = validate_float_range(None)
        assert is_valid is False
        assert "required" in error

    def test_validate_float_range_invalid_type(self):
        """Test validating non-numeric value."""
        is_valid, error = validate_float_range("invalid")
        assert is_valid is False
        assert "number" in error

    def test_validate_float_range_below_min(self):
        """Test validating value below minimum."""
        is_valid, error = validate_float_range(5.0, min_value=10.0)
        assert is_valid is False
        assert "at least 10.0" in error

    def test_validate_float_range_above_max(self):
        """Test validating value above maximum."""
        is_valid, error = validate_float_range(150.0, max_value=100.0)
        assert is_valid is False
        assert "at most 100.0" in error

    def test_validate_float_range_edge_min(self):
        """Test validating value at minimum."""
        is_valid, error = validate_float_range(10.0, min_value=10.0)
        assert is_valid is True
        assert error is None

    def test_validate_float_range_edge_max(self):
        """Test validating value at maximum."""
        is_valid, error = validate_float_range(100.0, max_value=100.0)
        assert is_valid is True
        assert error is None

    def test_validate_float_range_no_limits(self):
        """Test validating without min/max limits."""
        is_valid, error = validate_float_range(999.999)
        assert is_valid is True
        assert error is None

    def test_validate_float_range_converts_int(self):
        """Test that integers are converted to float."""
        is_valid, error = validate_float_range(42, min_value=0.0, max_value=100.0)
        assert is_valid is True
        assert error is None

    def test_validate_float_range_converts_string(self):
        """Test that numeric strings are converted."""
        is_valid, error = validate_float_range("42.5", min_value=0.0, max_value=100.0)
        assert is_valid is True
        assert error is None


class TestValidateIntegerRange:
    """Tests for integer range validation."""

    def test_validate_integer_range_valid(self):
        """Test validating valid integer."""
        is_valid, error = validate_integer_range(50, min_value=0, max_value=100)
        assert is_valid is True
        assert error is None

    def test_validate_integer_range_none(self):
        """Test validating None value."""
        is_valid, error = validate_integer_range(None)
        assert is_valid is False
        assert "required" in error

    def test_validate_integer_range_invalid_type(self):
        """Test validating non-integer value."""
        is_valid, error = validate_integer_range("invalid")
        assert is_valid is False
        assert "integer" in error

    def test_validate_integer_range_below_min(self):
        """Test validating value below minimum."""
        is_valid, error = validate_integer_range(5, min_value=10)
        assert is_valid is False
        assert "at least 10" in error

    def test_validate_integer_range_above_max(self):
        """Test validating value above maximum."""
        is_valid, error = validate_integer_range(150, max_value=100)
        assert is_valid is False
        assert "at most 100" in error

    def test_validate_integer_range_edge_min(self):
        """Test validating value at minimum."""
        is_valid, error = validate_integer_range(10, min_value=10)
        assert is_valid is True
        assert error is None

    def test_validate_integer_range_edge_max(self):
        """Test validating value at maximum."""
        is_valid, error = validate_integer_range(100, max_value=100)
        assert is_valid is True
        assert error is None

    def test_validate_integer_range_no_limits(self):
        """Test validating without min/max limits."""
        is_valid, error = validate_integer_range(999)
        assert is_valid is True
        assert error is None

    def test_validate_integer_range_converts_string(self):
        """Test that numeric strings are converted."""
        is_valid, error = validate_integer_range("42", min_value=0, max_value=100)
        assert is_valid is True
        assert error is None

    def test_validate_integer_range_converts_float(self):
        """Test that floats are converted to integers."""
        is_valid, error = validate_integer_range(42.9, min_value=0, max_value=100)
        assert is_valid is True
        assert error is None


class TestValidateHeatingType:
    """Tests for heating type validation."""

    def test_validate_heating_type_radiator(self):
        """Test validating radiator heating type."""
        is_valid, error = validate_heating_type("radiator")
        assert is_valid is True
        assert error is None

    def test_validate_heating_type_floor_heating(self):
        """Test validating floor_heating type."""
        is_valid, error = validate_heating_type("floor_heating")
        assert is_valid is True
        assert error is None

    def test_validate_heating_type_airco(self):
        """Test validating airco type."""
        is_valid, error = validate_heating_type("airco")
        assert is_valid is True
        assert error is None

    def test_validate_heating_type_invalid(self):
        """Test validating invalid heating type."""
        is_valid, error = validate_heating_type("invalid_type")
        assert is_valid is False
        assert "radiator, floor_heating, airco" in error

    def test_validate_heating_type_none(self):
        """Test validating None value."""
        is_valid, error = validate_heating_type(None)
        assert is_valid is False
        assert "required" in error

    def test_validate_heating_type_empty(self):
        """Test validating empty string."""
        is_valid, error = validate_heating_type("")
        assert is_valid is False
        assert "required" in error

    def test_validate_heating_type_not_string(self):
        """Test validating non-string value."""
        is_valid, error = validate_heating_type(123)
        assert is_valid is False
        assert "string" in error

    def test_validate_heating_type_case_sensitive(self):
        """Test that validation is case sensitive."""
        is_valid, error = validate_heating_type("RADIATOR")
        assert is_valid is False
        assert "radiator, floor_heating, airco" in error


class TestValidateHvacMode:
    """Tests for HVAC mode validation."""

    def test_validate_hvac_mode_off(self):
        """Test validating off mode."""
        is_valid, error = validate_hvac_mode("off")
        assert is_valid is True
        assert error is None

    def test_validate_hvac_mode_heat(self):
        """Test validating heat mode."""
        is_valid, error = validate_hvac_mode("heat")
        assert is_valid is True
        assert error is None

    def test_validate_hvac_mode_cool(self):
        """Test validating cool mode."""
        is_valid, error = validate_hvac_mode("cool")
        assert is_valid is True
        assert error is None

    def test_validate_hvac_mode_auto(self):
        """Test validating auto mode."""
        is_valid, error = validate_hvac_mode("auto")
        assert is_valid is True
        assert error is None

    def test_validate_hvac_mode_invalid(self):
        """Test validating invalid HVAC mode."""
        is_valid, error = validate_hvac_mode("invalid_mode")
        assert is_valid is False
        assert "off, heat, cool, auto" in error

    def test_validate_hvac_mode_none(self):
        """Test validating None value."""
        is_valid, error = validate_hvac_mode(None)
        assert is_valid is False
        assert "required" in error

    def test_validate_hvac_mode_empty(self):
        """Test validating empty string."""
        is_valid, error = validate_hvac_mode("")
        assert is_valid is False
        assert "required" in error

    def test_validate_hvac_mode_not_string(self):
        """Test validating non-string value."""
        is_valid, error = validate_hvac_mode(123)
        assert is_valid is False
        assert "string" in error

    def test_validate_hvac_mode_case_sensitive(self):
        """Test that validation is case sensitive."""
        is_valid, error = validate_hvac_mode("HEAT")
        assert is_valid is False
        assert "off, heat, cool, auto" in error


class TestSanitizeStringInput:
    """Tests for string input sanitization."""

    def test_sanitize_string_input_valid(self):
        """Test sanitizing valid string."""
        is_valid, error = sanitize_string_input("living_room")
        assert is_valid is True
        assert error is None

    def test_sanitize_string_input_none(self):
        """Test sanitizing None value."""
        is_valid, error = sanitize_string_input(None)
        assert is_valid is False
        assert "required" in error

    def test_sanitize_string_input_not_string(self):
        """Test sanitizing non-string value."""
        is_valid, error = sanitize_string_input(123)
        assert is_valid is False
        assert "string" in error

    def test_sanitize_string_input_too_long(self):
        """Test sanitizing string exceeding max length."""
        is_valid, error = sanitize_string_input("a" * 256)
        assert is_valid is False
        assert "255 characters" in error

    def test_sanitize_string_input_custom_max_length(self):
        """Test sanitizing with custom max length."""
        is_valid, error = sanitize_string_input("test", max_length=3)
        assert is_valid is False
        assert "3 characters" in error

    def test_sanitize_string_input_script_tag(self):
        """Test detecting script tag."""
        is_valid, error = sanitize_string_input("<script>alert('xss')</script>")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "<script" in error

    def test_sanitize_string_input_javascript_protocol(self):
        """Test detecting javascript protocol."""
        is_valid, error = sanitize_string_input("javascript:alert('xss')")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "javascript:" in error

    def test_sanitize_string_input_onerror(self):
        """Test detecting onerror event."""
        is_valid, error = sanitize_string_input("img onerror=alert('xss')")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "onerror=" in error

    def test_sanitize_string_input_onload(self):
        """Test detecting onload event."""
        is_valid, error = sanitize_string_input("body onload=malicious()")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "onload=" in error

    def test_sanitize_string_input_eval(self):
        """Test detecting eval function."""
        is_valid, error = sanitize_string_input("eval(malicious_code)")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "eval(" in error

    def test_sanitize_string_input_expression(self):
        """Test detecting expression function."""
        is_valid, error = sanitize_string_input("expression(alert('xss'))")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "expression(" in error

    def test_sanitize_string_input_path_traversal_forward(self):
        """Test detecting path traversal with forward slashes."""
        is_valid, error = sanitize_string_input("../../etc/passwd")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "../" in error

    def test_sanitize_string_input_path_traversal_backward(self):
        """Test detecting path traversal with backslashes."""
        is_valid, error = sanitize_string_input("..\\..\\windows\\system32")
        assert is_valid is False
        assert "suspicious pattern" in error
        assert "..\\" in error

    def test_sanitize_string_input_case_insensitive(self):
        """Test that detection is case insensitive."""
        is_valid, error = sanitize_string_input("<SCRIPT>alert('xss')</SCRIPT>")
        assert is_valid is False
        assert "suspicious pattern" in error

    def test_sanitize_string_input_mixed_case(self):
        """Test detecting mixed case JavaScript."""
        is_valid, error = sanitize_string_input("JaVaScRiPt:alert(1)")
        assert is_valid is False
        assert "suspicious pattern" in error

    def test_sanitize_string_input_max_length_edge(self):
        """Test string at max length is valid."""
        is_valid, error = sanitize_string_input("a" * 255)
        assert is_valid is True
        assert error is None

    def test_sanitize_string_input_normal_text(self):
        """Test normal text with numbers and special chars."""
        is_valid, error = sanitize_string_input("Room-123_test!@#")
        assert is_valid is True
        assert error is None
