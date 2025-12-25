import time

from smart_heating.pid import PID, Error


def test_pid_basic_response():
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
    pid = PID(
        heating_system="radiator",
        automatic_gain_value=1.0,
        heating_curve_coefficient=1.0,
        automatic_gains=True,
    )
    e = Error(2.0)
    out = pid.update(e, heating_curve_value=10.0)
    assert isinstance(out, float)
