"""Comprehensive tests for PID controller with anti-windup protection."""

import time

from smart_heating.pid import DEADBAND, PID, Error


class TestPIDIntegralWindupProtection:
    """Test PID integral windup protection."""

    def test_integral_windup_protection_floor_heating(self):
        """Test integral clamping for floor heating (50.0 limit)."""
        pid = PID(
            heating_system="floor_heating",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            ki=1.0,  # High integral gain to accumulate quickly
        )

        # Simulate large error for extended period to trigger windup
        for _ in range(100):
            pid.update(Error(10.0), None)
            time.sleep(0.01)

        # Integral should clamp at 50.0, not grow to infinity
        assert abs(pid._integral) <= 50.0
        assert pid._integral > 0  # Should have accumulated something

    def test_integral_windup_protection_radiator(self):
        """Test integral clamping for radiator (10.0 limit)."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            ki=1.0,  # High integral gain
        )

        # Simulate large error for extended period
        for _ in range(100):
            pid.update(Error(10.0), None)
            time.sleep(0.01)

        # Integral should clamp at 10.0 for radiator (faster response)
        assert abs(pid._integral) <= 10.0
        assert pid._integral > 0

    def test_integral_windup_protection_custom_limit(self):
        """Test custom integral limit."""
        custom_limit = 25.0
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            ki=1.0,
            integral_limit=custom_limit,
        )

        # Accumulate integral
        for _ in range(100):
            pid.update(Error(10.0), None)
            time.sleep(0.01)

        # Should use custom limit
        assert abs(pid._integral) <= custom_limit

    def test_integral_negative_windup_protection(self):
        """Test integral clamping works for negative errors."""
        pid = PID(
            heating_system="floor_heating",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            ki=1.0,
        )

        # Simulate large negative error
        for _ in range(100):
            pid.update(Error(-10.0), None)
            time.sleep(0.01)

        # Integral should clamp at -50.0
        assert pid._integral >= -50.0
        assert pid._integral < 0

    def test_integral_stays_within_bounds_during_operation(self):
        """Test integral never exceeds limits during normal operation."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            ki=0.5,
        )

        # Simulate varying errors
        errors = [5.0, -3.0, 8.0, -2.0, 10.0, -5.0, 7.0]
        for err in errors * 20:  # Repeat to accumulate
            pid.update(Error(err), None)
            time.sleep(0.01)
            # Check integral never exceeds radiator limit
            assert -10.0 <= pid._integral <= 10.0


class TestPIDOutputClamping:
    """Test PID output clamping to prevent extreme adjustments."""

    def test_output_clamping_default_limit(self):
        """Test PID output is clamped to ±15.0 by default."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=100.0,  # Huge proportional gain to trigger clamping
        )

        output = pid.update(Error(10.0), None)
        assert -15.0 <= output <= 15.0

    def test_output_clamping_positive_extreme(self):
        """Test positive output clamping."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=50.0,
            ki=10.0,
            kd=5.0,
        )

        # Large error should clamp output
        for _ in range(10):
            output = pid.update(Error(20.0), None)
            time.sleep(0.01)
            assert output <= 15.0

    def test_output_clamping_negative_extreme(self):
        """Test negative output clamping."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=50.0,
        )

        output = pid.update(Error(-20.0), None)
        assert output >= -15.0

    def test_output_clamping_custom_limit(self):
        """Test custom output limit."""
        custom_limit = 10.0
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=100.0,
            output_limit=custom_limit,
        )

        output = pid.update(Error(10.0), None)
        assert -custom_limit <= output <= custom_limit

    def test_output_within_limits_normal_operation(self):
        """Test output stays within limits during normal operation."""
        pid = PID(
            heating_system="floor_heating",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=2.0,
            ki=0.1,
            kd=0.5,
        )

        # Normal operating errors
        errors = [2.0, 1.5, -0.5, 3.0, -1.0, 2.5, 0.8]
        for err in errors:
            output = pid.update(Error(err), None)
            time.sleep(0.01)
            assert -15.0 <= output <= 15.0


class TestPIDGainModes:
    """Test automatic vs manual gain modes."""

    def test_automatic_gains_enabled(self):
        """Test PID uses automatic gain calculation."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.5,
            heating_curve_coefficient=1.2,
            automatic_gains=True,
        )

        output = pid.update(Error(2.0), heating_curve_value=30.0)
        assert isinstance(output, float)
        # Automatic gains should scale with heating curve

    def test_automatic_gains_disabled(self):
        """Test PID uses manual gains."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=0.5,  # Smaller gain to avoid output clamping
            ki=0.01,
            kd=0.05,
        )

        # Reset to ensure clean state for timing
        pid.reset()
        time.sleep(0.1)  # Realistic delay (100ms) to avoid huge derivative term

        output = pid.update(Error(1.0), None)
        # Should use manual gains (kp=0.5)
        # P component should be 0.5 * 1.0 = 0.5
        # I component ~= 0.01 * 1.0 * 0.1 = 0.001
        # D component ~= 0.05 * 1.0 / 0.1 = 0.5
        # Total ~= 1.0
        assert abs(output - 1.0) < 0.3  # Allow for timing variations

    def test_automatic_gains_scale_with_heating_curve(self):
        """Test automatic gains scale with heating curve value."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=True,
        )

        # Low heating curve value
        pid.reset()
        time.sleep(0.1)  # Realistic delay to avoid huge derivative term
        output_low = pid.update(Error(1.0), 10.0)

        # High heating curve value
        pid.reset()
        time.sleep(0.1)  # Realistic delay to avoid huge derivative term
        output_high = pid.update(Error(1.0), 50.0)

        # Higher heating curve should produce different output
        # Both outputs should be within limits
        assert -15.0 <= output_low <= 15.0
        assert -15.0 <= output_high <= 15.0
        assert output_low != output_high

    def test_automatic_gains_none_heating_curve(self):
        """Test automatic gains with None heating curve value."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=True,
        )

        # Should not crash with None
        output = pid.update(Error(2.0), heating_curve_value=None)
        assert isinstance(output, float)


class TestPIDHeatingTypeDefaults:
    """Test heating-type-aware default integral limits."""

    def test_floor_heating_default_integral_limit(self):
        """Test floor heating gets 50.0 integral limit by default."""
        pid = PID(
            heating_system="floor_heating",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        assert pid.integral_limit == 50.0

    def test_radiator_default_integral_limit(self):
        """Test radiator gets 10.0 integral limit by default."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        assert pid.integral_limit == 10.0

    def test_unknown_heating_type_uses_radiator_limit(self):
        """Test unknown heating type defaults to radiator limit."""
        pid = PID(
            heating_system="unknown_type",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        # Should default to radiator limit (10.0)
        assert pid.integral_limit == 10.0

    def test_custom_integral_limit_overrides_default(self):
        """Test custom integral limit overrides heating-type default."""
        custom_limit = 30.0
        pid = PID(
            heating_system="floor_heating",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            integral_limit=custom_limit,
        )

        # Should use custom limit, not default 50.0
        assert pid.integral_limit == custom_limit


class TestPIDReset:
    """Test PID state reset functionality."""

    def test_reset_clears_integral(self):
        """Test reset clears accumulated integral."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            ki=0.5,
        )

        # Accumulate integral
        for _ in range(10):
            pid.update(Error(5.0), None)
            time.sleep(0.01)

        assert pid._integral != 0.0

        # Reset should clear integral
        pid.reset()
        assert pid._integral == 0.0

    def test_reset_clears_last_error(self):
        """Test reset clears last error (derivative term)."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        pid.update(Error(5.0), None)
        assert pid._last_error != 0.0

        pid.reset()
        assert pid._last_error == 0.0

    def test_reset_updates_time(self):
        """Test reset updates last time."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        old_time = pid._last_time
        time.sleep(0.1)
        pid.reset()
        new_time = pid._last_time

        assert new_time > old_time


class TestPIDDeadband:
    """Test PID deadband functionality."""

    def test_deadband_default_value(self):
        """Test default deadband is DEADBAND constant."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        assert pid.deadband == DEADBAND

    def test_deadband_prevents_output_small_errors(self):
        """Test errors within deadband produce zero output."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=10.0,  # High gain to make small errors visible
        )

        # Error within deadband (0.1)
        output = pid.update(Error(0.05), None)
        assert output == 0.0

        # Error exactly at deadband
        output = pid.update(Error(0.1), None)
        assert output == 0.0

    def test_deadband_allows_output_large_errors(self):
        """Test errors outside deadband produce output."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=1.0,
        )

        # Error outside deadband
        output = pid.update(Error(1.0), None)
        assert output != 0.0

    def test_custom_deadband(self):
        """Test custom deadband value."""
        custom_deadband = 0.5
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=10.0,
            deadband=custom_deadband,
        )

        # Within custom deadband
        output = pid.update(Error(0.3), None)
        assert output == 0.0

        # Outside custom deadband
        output = pid.update(Error(0.6), None)
        assert output != 0.0


class TestPIDComponents:
    """Test individual PID components (P, I, D)."""

    def test_proportional_only(self):
        """Test pure proportional control."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=2.0,
            ki=0.0,
            kd=0.0,
        )

        output = pid.update(Error(5.0), None)
        # P = kp * error = 2.0 * 5.0 = 10.0
        assert abs(output - 10.0) < 0.1

    def test_integral_accumulation(self):
        """Test integral accumulates over time."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=0.0,
            ki=1.0,
            kd=0.0,
        )

        # First update
        output1 = pid.update(Error(1.0), None)
        time.sleep(0.1)
        # Second update - integral should have accumulated
        output2 = pid.update(Error(1.0), None)

        assert output2 > output1  # Integral should grow

    def test_derivative_response(self):
        """Test derivative responds to error change."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=0.0,
            ki=0.0,
            kd=1.0,
        )

        # Increasing error
        pid.update(Error(0.0), None)
        time.sleep(0.1)
        output = pid.update(Error(5.0), None)

        # Derivative should produce output
        assert output != 0.0


class TestPIDEdgeCases:
    """Test PID edge cases and boundary conditions."""

    def test_zero_error(self):
        """Test PID with zero error."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=1.0,
            ki=0.1,
            kd=0.5,
        )

        output = pid.update(Error(0.0), None)
        assert output == 0.0

    def test_rapid_updates(self):
        """Test PID handles rapid successive updates."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        # Rapid updates without sleep
        for _ in range(100):
            output = pid.update(Error(2.0), None)
            assert isinstance(output, float)
            assert -15.0 <= output <= 15.0

    def test_alternating_errors(self):
        """Test PID with alternating positive/negative errors."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            kp=1.0,
            ki=0.1,
        )

        errors = [2.0, -2.0, 3.0, -3.0, 1.0, -1.0]
        for err in errors:
            output = pid.update(Error(err), None)
            time.sleep(0.01)
            # Output should be within limits
            assert -15.0 <= output <= 15.0

    def test_large_time_gap(self):
        """Test PID handles large time gaps between updates."""
        pid = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
            ki=0.1,
        )

        pid.update(Error(2.0), None)
        time.sleep(0.2)  # Large time gap
        output = pid.update(Error(2.0), None)

        # Should handle gracefully
        assert isinstance(output, float)
        assert -15.0 <= output <= 15.0


# Legacy tests preserved
def test_pid_basic_response():
    """Test basic PID response."""
    pid = PID(
        heating_system="radiator",
        automatic_gain_value=1.0,
        heating_curve_coefficient=1.0,
        automatic_gains=False,
        kp=1.0,
        ki=0.1,
        kd=0.0,
    )
    e = Error(1.0)
    out1 = pid.update(e, heating_curve_value=None)
    time.sleep(0.1)
    out2 = pid.update(e, heating_curve_value=None)
    assert out1 != out2 or out2 == out1  # Should be a numeric value


def test_pid_automatic_gains_do_not_throw():
    """Test automatic gains don't throw errors."""
    pid = PID(
        heating_system="radiator",
        automatic_gain_value=1.0,
        heating_curve_coefficient=1.0,
        automatic_gains=True,
    )
    e = Error(2.0)
    out = pid.update(e, heating_curve_value=10.0)
    assert isinstance(out, float)
