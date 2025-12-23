from smart_heating.heating_curve import HeatingCurve
from smart_heating.pwm import PWM, CycleConfig
import pytest


def test_pwm_duty_cycle_basic():
    hc = HeatingCurve(heating_system="radiator", coefficient=1.0)
    pwm = PWM(cycles=CycleConfig(), heating_curve=hc)
    pwm.enable()
    pwm.update(60.0, 50.0)
    assert pwm.duty_cycle is not None


def test_pwm_disabled_and_reset_and_setpoint():
    hc = HeatingCurve(heating_system="radiator", coefficient=1.0)
    pwm = PWM(
        cycles=CycleConfig(
            min_on_seconds=10, max_on_seconds=100, min_off_seconds=5, max_off_seconds=50
        ),
        heating_curve=hc,
    )

    # Disabled: duty_cycle returns None
    assert pwm.duty_cycle is None

    pwm.enable()
    pwm.update(40.0, 50.0)
    assert pwm.duty_cycle is not None
    before = pwm.duty_cycle

    # setpoint should be calculable once duty cycle percentage is set
    sp = pwm.setpoint
    if sp is not None:
        assert isinstance(sp, float)

    # Reset should clear and return to min values
    pwm.reset()
    assert pwm.last_duty_cycle_percentage is None
    pwm.enable()
    pwm.update(10.0, 20.0)
    # Ensure on/off are within configured bounds
    on, off = pwm.duty_cycle
    assert on >= 10 and on <= 100
    assert off >= 5 and off <= 50


def test_pwm_clamping_on_off_and_setpoint_formula():
    hc = HeatingCurve(heating_system="radiator", coefficient=1.0)
    # Populate hc.value via update so that value and base_offset are consistent
    hc.update(30.0, -5.0)
    cycles = CycleConfig(
        min_on_seconds=1, max_on_seconds=200, min_off_seconds=1, max_off_seconds=200
    )

    pwm = PWM(cycles=cycles, heating_curve=hc)
    pwm.enable()

    # Very high requested_setpoint -> duty cycle should clamp to max
    pwm.update(100.0, 20.0)
    on, off = pwm.duty_cycle
    assert on == cycles.max_on_seconds
    assert off == cycles.min_off_seconds

    # Check setpoint formula: manual calculation
    pct = pwm.last_duty_cycle_percentage
    expected = hc.base_offset + ((pct / 4) * (hc.value - hc.base_offset)) if hc.value else None
    if expected is not None:
        assert pytest.approx(expected, rel=1e-3) == pwm.setpoint


def test_pwm_disabled_and_reset_behavior():
    hc = HeatingCurve(heating_system="radiator", coefficient=1.0)
    hc.update(22.0, 0.0)
    cycles = CycleConfig(
        min_on_seconds=5, max_on_seconds=100, min_off_seconds=5, max_off_seconds=100
    )

    pwm = PWM(cycles=cycles, heating_curve=hc)

    # Initially disabled -> no duty cycle
    assert pwm.duty_cycle is None

    # Enable and update should produce on/off seconds
    pwm.enable()
    pwm.update(30.0, 40.0)
    assert pwm.duty_cycle is not None

    # Reset should clear last duty cycle percentage and restore defaults
    pwm.reset()
    assert pwm.last_duty_cycle_percentage is None
    # after reset, even if enabled, duty_cycle uses last on/off seconds (reset to min)
    assert pwm.duty_cycle == (cycles.min_on_seconds, cycles.min_off_seconds)
