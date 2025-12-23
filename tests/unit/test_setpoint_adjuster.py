"""Tests for SetpointAdjuster."""

from smart_heating.setpoint_adjuster import SetpointAdjuster


def test_calculate_offset_basic():
    s = SetpointAdjuster()

    # Centered 0.5 -> offset 0
    assert s.calculate_offset(0.5) == 0.0
    assert s.offset == 0.0

    # 0 -> negative offset
    off = s.calculate_offset(0.0)
    assert off < 0

    # >1 should be clamped to 1
    off2 = s.calculate_offset(2.0)
    assert off2 > 0

    # <0 should be clamped to 0
    off3 = s.calculate_offset(-1.0)
    assert off3 < 0
