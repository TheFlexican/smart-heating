"""Tests for ManualOverrideDetector."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.core.coordination.manual_override_detector import ManualOverrideDetector
from smart_heating.models import Area


@pytest.fixture
def area_manager():
    """Create a mock area manager."""
    manager = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def sample_area():
    """Create a sample area for testing."""
    area = MagicMock(spec=Area)
    area.area_id = "living_room"
    area.name = "Living Room"
    area.devices = {"climate.thermostat_lr": {"type": "thermostat"}}
    area.get_effective_target_temperature = MagicMock(return_value=20.0)
    area.target_temperature = 20.0
    area.manual_override = False
    return area


class TestManualOverrideDetector:
    """Test ManualOverrideDetector functionality."""

    def test_init_default(self):
        """Test initialization with default values."""
        detector = ManualOverrideDetector()
        assert detector._startup_grace_period is False

    def test_init_with_grace_period(self):
        """Test initialization with startup grace period active."""
        detector = ManualOverrideDetector(startup_grace_period_active=True)
        assert detector._startup_grace_period is True

    def test_set_startup_grace_period(self):
        """Test setting startup grace period."""
        detector = ManualOverrideDetector(startup_grace_period_active=True)
        assert detector._startup_grace_period is True

        detector.set_startup_grace_period(False)
        assert detector._startup_grace_period is False

    @pytest.mark.asyncio
    async def test_detect_during_grace_period(self, area_manager, sample_area):
        """Test that manual override is not detected during grace period."""
        detector = ManualOverrideDetector(startup_grace_period_active=True)
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})

        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", 21.0, area_manager
        )

        assert result is False
        assert sample_area.manual_override is False
        area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_none_temperature(self, area_manager, sample_area):
        """Test that None temperature is ignored."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})

        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", None, area_manager
        )

        assert result is False
        assert sample_area.manual_override is False
        area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_no_area_found(self, area_manager):
        """Test behavior when no area contains the device."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={})

        result = await detector.async_detect_and_apply_override(
            "climate.unknown", 21.0, area_manager
        )

        assert result is False
        area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_matching_expected_temperature(self, area_manager, sample_area):
        """Test that temperature matching expected target is not considered manual."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})
        sample_area.get_effective_target_temperature.return_value = 20.0

        # Set temperature to expected value (within tolerance)
        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", 20.05, area_manager
        )

        assert result is False
        assert sample_area.manual_override is False
        area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_stale_lower_temperature(self, area_manager, sample_area):
        """Test that lower temperatures are ignored as stale state changes."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})
        sample_area.get_effective_target_temperature.return_value = 20.0

        # Set temperature lower than expected
        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", 18.0, area_manager
        )

        assert result is False
        assert sample_area.manual_override is False
        area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_detect_manual_override_higher_temp(self, area_manager, sample_area):
        """Test that higher temperature triggers manual override."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})
        sample_area.get_effective_target_temperature.return_value = 20.0

        # Set temperature higher than expected
        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", 22.0, area_manager
        )

        assert result is True
        assert sample_area.manual_override is True
        assert sample_area.target_temperature == 22.0
        area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_manual_override_different_temp(self, area_manager, sample_area):
        """Test that significantly different temperature triggers manual override."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})
        sample_area.get_effective_target_temperature.return_value = 20.0

        # Set temperature different from expected (outside tolerance)
        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", 21.5, area_manager
        )

        assert result is True
        assert sample_area.manual_override is True
        assert sample_area.target_temperature == 21.5
        area_manager.async_save.assert_called_once()

    def test_find_area_for_device(self, area_manager, sample_area):
        """Test finding area for a device."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas.return_value = {"living_room": sample_area}

        area = detector._find_area_for_device("climate.thermostat_lr", area_manager)

        assert area == sample_area

    def test_find_area_for_device_not_found(self, area_manager, sample_area):
        """Test finding area when device is not in any area."""
        detector = ManualOverrideDetector()
        area_manager.get_all_areas.return_value = {"living_room": sample_area}

        area = detector._find_area_for_device("climate.unknown", area_manager)

        assert area is None

    def test_is_manual_change_matches_expected(self, sample_area):
        """Test manual change detection when temperature matches expected."""
        detector = ManualOverrideDetector()
        sample_area.get_effective_target_temperature.return_value = 20.0

        is_manual = detector._is_manual_change("climate.thermostat_lr", 20.05, sample_area)

        assert is_manual is False

    def test_is_manual_change_lower_than_expected(self, sample_area):
        """Test manual change detection when temperature is lower than expected."""
        detector = ManualOverrideDetector()
        sample_area.get_effective_target_temperature.return_value = 20.0

        is_manual = detector._is_manual_change("climate.thermostat_lr", 18.0, sample_area)

        assert is_manual is False

    def test_is_manual_change_higher_than_expected(self, sample_area):
        """Test manual change detection when temperature is higher than expected."""
        detector = ManualOverrideDetector()
        sample_area.get_effective_target_temperature.return_value = 20.0

        is_manual = detector._is_manual_change("climate.thermostat_lr", 22.0, sample_area)

        assert is_manual is True

    @pytest.mark.asyncio
    async def test_apply_override(self, area_manager, sample_area):
        """Test applying manual override to an area."""
        detector = ManualOverrideDetector()
        sample_area.get_effective_target_temperature.return_value = 20.0

        await detector._apply_override("climate.thermostat_lr", 22.0, sample_area, area_manager)

        assert sample_area.manual_override is True
        assert sample_area.target_temperature == 22.0
        area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_idle_setpoint_above_target_not_manual_override(self, area_manager, sample_area):
        """Test that idle setpoint above target is not falsely detected as manual override.

        When the room is in idle state and current_temp is above the schedule target,
        the system intentionally sets the thermostat to current_temp to prevent unnecessary
        heating cycles. This should NOT be detected as a manual override.

        Example scenario:
        - Schedule target: 20.1°C
        - Current room temp: 20.5°C
        - Hysteresis: 0.5°C
        - System sets thermostat to 20.5°C (current temp) during idle
        - This should NOT trigger manual override!
        """
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})

        # Setup: target from schedule is 20.1°C, current temp is 20.5°C
        sample_area.get_effective_target_temperature.return_value = 20.1
        sample_area.current_temperature = 20.5
        sample_area.hysteresis_override = None  # Use default
        area_manager.hysteresis = 0.5  # Default hysteresis

        # The system sets thermostat to current_temp (20.5°C) during idle state
        # This should NOT be detected as manual override
        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", 20.5, area_manager
        )

        # This should NOT trigger manual override - it's an automated idle setpoint
        assert result is False
        assert sample_area.manual_override is False
        area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_idle_setpoint_slightly_above_target_not_manual_override(
        self, area_manager, sample_area
    ):
        """Test idle setpoint just above target is not falsely detected as manual.

        When current_temp is just slightly above target (e.g., 0.4°C above with 0.5 hysteresis),
        the idle setpoint logic sets thermostat to current_temp. This should not be
        falsely detected as a manual change.
        """
        detector = ManualOverrideDetector()
        area_manager.get_all_areas = MagicMock(return_value={"living_room": sample_area})

        # Setup: target is 20.0°C, current temp is 20.4°C (within idle range)
        sample_area.get_effective_target_temperature.return_value = 20.0
        sample_area.current_temperature = 20.4
        sample_area.hysteresis_override = None
        area_manager.hysteresis = 0.5

        # System sets thermostat to current_temp during idle
        result = await detector.async_detect_and_apply_override(
            "climate.thermostat_lr", 20.4, area_manager
        )

        assert result is False
        assert sample_area.manual_override is False
        area_manager.async_save.assert_not_called()
