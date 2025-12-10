import pytest
from smart_heating.overshoot_protection import OvershootProtection


class FakeCoordinator:
    async def async_set_control_max_relative_modulation(self, value):
        pass

    @property
    def boiler_temperature(self):
        return 45.0


@pytest.mark.asyncio
async def test_calculate_returns_none_with_no_setter():
    # Coordinator without modulation control
    class Coord2:
        pass

    op = OvershootProtection(Coord2(), "radiator")
    assert await op.calculate() is None
