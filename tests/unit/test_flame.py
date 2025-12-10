from smart_heating.flame import Flame, FlameStatus


def test_flame_basic_tracking():
    f = Flame()
    f.update(True)
    f.update(False)
    # After toggling, health status should be set (HEALTHY or SHORT_CYCLING)
    assert f.health_status in (FlameStatus.HEALTHY, FlameStatus.SHORT_CYCLING)
