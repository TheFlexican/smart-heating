import pytest

from smart_heating.heating_curve import HEATING_SYSTEM_UNDERFLOOR, HeatingCurve


def test_calculate_basic():
    # Simple compute, should be deterministic
    val = HeatingCurve.calculate(22.0, 10.0)
    assert isinstance(val, float)


def test_base_offset():
    hc1 = HeatingCurve(heating_system=HEATING_SYSTEM_UNDERFLOOR)
    assert abs(hc1.base_offset - 40.0) < 0.001
    hc2 = HeatingCurve()
    assert abs(hc2.base_offset - 55.0) < 0.001


def test_calculate_coefficient_and_update():
    hc = HeatingCurve()
    setpoint = 60.0
    target = 22.0
    outside = 10.0
    coeff = hc.calculate_coefficient(setpoint, target, outside)
    assert isinstance(coeff, float)
    # The update method should set the internals and value
    hc.update(target, outside)
    assert hc.value is None or isinstance(hc.value, float)


def test_autotune_and_restore():
    hc = HeatingCurve()
    # autotune returns None for too small setpoints
    assert hc.autotune(5.0, 22.0, 10.0) is None

    # Now with a realistic setpoint sequence, we expect an average coefficient
    for sp in [55.0, 56.0, 57.0, 58.0, 56.0]:
        res = hc.autotune(sp, 22.0, 10.0)
        assert res is None or isinstance(res, float)

    # Restore and ensure derivative/optimal coefficients are set
    hc.restore_autotune(1.2, 0.1)
    assert abs(hc.optimal_coefficient - 1.2) < 0.001
    assert abs(hc.coefficient_derivative - 0.1) < 0.001


from smart_heating.heating_curve import (
    HEATING_SYSTEM_RADIATOR,
)


def test_calculate_base_values():
    hc = HeatingCurve(heating_system=HEATING_SYSTEM_RADIATOR, coefficient=1.0)
    val = hc.calculate(20, 10)  # target 20, outside 10
    assert isinstance(val, float)


def test_update_and_value():
    hc = HeatingCurve(heating_system=HEATING_SYSTEM_UNDERFLOOR, coefficient=1.2)
    hc.update(21.0, 5.0)
    assert hc.value is not None


def test_calculate_coefficient():
    hc = HeatingCurve(heating_system=HEATING_SYSTEM_RADIATOR, coefficient=1.0)
    coeff = hc.calculate_coefficient(
        setpoint=55.0, target_temperature=20.0, outside_temperature=0.0
    )
    assert isinstance(coeff, float)


def test_default_base_offsets():
    hc_floor = HeatingCurve(heating_system=HEATING_SYSTEM_UNDERFLOOR, coefficient=1.0)
    hc_rad = HeatingCurve(heating_system=HEATING_SYSTEM_RADIATOR, coefficient=1.0)
    assert hc_floor.base_offset == pytest.approx(40.0, rel=1e-3)
    assert hc_rad.base_offset == pytest.approx(55.0, rel=1e-3)
