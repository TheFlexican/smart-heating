"""Comprehensive tests for area-level PID controller manager."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from smart_heating.climate.controllers.pid_controller_manager import (
    _get_current_area_mode,
    _clear_pid_state,
    _should_apply_pid,
    apply_pid_adjustment,
    _pids,
)
from smart_heating.pid import PID


@pytest.fixture
def mock_area():
    """Create a mock area for testing."""
    area = Mock()
    area.area_id = "test_area"
    area.name = "Test Area"
    area.target_temperature = 21.0
    area.current_temperature = 20.0
    area.preset_mode = "none"
    area.pid_enabled = False
    area.pid_automatic_gains = True
    area.pid_active_modes = ["schedule", "home", "comfort"]
    area.heating_type = "radiator"
    area.heating_curve_coefficient = 1.5

    # Mock schedule manager
    area.schedule_manager = Mock()
    area.schedule_manager.is_schedule_active = Mock(return_value=False)

    return area


@pytest.fixture
def mock_area_manager():
    """Create a mock area manager for testing."""
    manager = Mock()
    manager.default_heating_curve_coefficient = 1.0
    return manager


@pytest.fixture(autouse=True)
def cleanup_pids():
    """Clear PID state before each test."""
    _pids.clear()
    yield
    _pids.clear()


class TestGetCurrentAreaMode:
    """Test mode detection logic."""

    def test_preset_mode_takes_priority(self, mock_area):
        """Test preset mode takes priority over schedule."""
        mock_area.preset_mode = "comfort"
        mock_area.schedule_manager.is_schedule_active.return_value = True

        mode = _get_current_area_mode(mock_area)
        assert mode == "comfort"

    def test_schedule_active_when_no_preset(self, mock_area):
        """Test schedule mode when no preset is set."""
        mock_area.preset_mode = "none"
        mock_area.schedule_manager.is_schedule_active.return_value = True

        mode = _get_current_area_mode(mock_area)
        assert mode == "schedule"

    def test_manual_mode_when_no_preset_or_schedule(self, mock_area):
        """Test manual mode when no preset or schedule."""
        mock_area.preset_mode = "none"
        mock_area.schedule_manager.is_schedule_active.return_value = False

        mode = _get_current_area_mode(mock_area)
        assert mode == "manual"

    def test_none_preset_treated_as_no_preset(self, mock_area):
        """Test 'none' preset is treated as no preset."""
        mock_area.preset_mode = "none"
        mock_area.schedule_manager.is_schedule_active.return_value = False

        mode = _get_current_area_mode(mock_area)
        assert mode == "manual"

    def test_various_preset_modes(self, mock_area):
        """Test various preset modes are detected."""
        presets = ["home", "away", "sleep", "comfort", "eco", "boost"]

        for preset in presets:
            mock_area.preset_mode = preset
            mode = _get_current_area_mode(mock_area)
            assert mode == preset


class TestClearPIDState:
    """Test PID state clearing."""

    def test_clear_existing_pid(self):
        """Test clearing existing PID controller."""
        # Create a PID in the global dict
        area_id = "test_area"
        _pids[area_id] = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        assert area_id in _pids

        _clear_pid_state(area_id)

        assert area_id not in _pids

    def test_clear_nonexistent_pid(self):
        """Test clearing PID that doesn't exist doesn't error."""
        area_id = "nonexistent"

        # Should not raise
        _clear_pid_state(area_id)

    def test_clear_pid_multiple_times(self):
        """Test clearing same PID multiple times is safe."""
        area_id = "test_area"
        _pids[area_id] = PID(
            heating_system="radiator",
            automatic_gain_value=1.0,
            heating_curve_coefficient=1.0,
            automatic_gains=False,
        )

        _clear_pid_state(area_id)
        _clear_pid_state(area_id)  # Second clear

        assert area_id not in _pids


class TestShouldApplyPID:
    """Test PID application decision logic."""

    def test_pid_disabled_returns_false(self, mock_area):
        """Test PID disabled returns False."""
        mock_area.pid_enabled = False
        mock_area.preset_mode = "home"  # Active mode

        result = _should_apply_pid(mock_area, "home")
        assert result is False

    def test_pid_enabled_active_mode_returns_true(self, mock_area):
        """Test PID enabled with active mode returns True."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home", "comfort"]

        result = _should_apply_pid(mock_area, "home")
        assert result is True

    def test_pid_enabled_inactive_mode_returns_false(self, mock_area):
        """Test PID enabled but inactive mode returns False."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home", "comfort"]

        result = _should_apply_pid(mock_area, "away")
        assert result is False

    def test_schedule_mode_in_active_modes(self, mock_area):
        """Test schedule mode is recognized when active."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["schedule", "home"]

        result = _should_apply_pid(mock_area, "schedule")
        assert result is True

    def test_manual_mode_not_in_active_modes(self, mock_area):
        """Test manual mode typically not in active modes."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["schedule", "home", "comfort"]

        result = _should_apply_pid(mock_area, "manual")
        assert result is False

    def test_multiple_active_modes(self, mock_area):
        """Test PID works with multiple active modes."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["schedule", "home", "comfort", "eco"]

        assert _should_apply_pid(mock_area, "schedule") is True
        assert _should_apply_pid(mock_area, "home") is True
        assert _should_apply_pid(mock_area, "comfort") is True
        assert _should_apply_pid(mock_area, "eco") is True
        assert _should_apply_pid(mock_area, "away") is False


class TestApplyPIDAdjustment:
    """Test PID adjustment application."""

    def test_pid_disabled_returns_original_candidate(self, mock_area, mock_area_manager):
        """Test PID disabled returns original candidate unchanged."""
        mock_area.pid_enabled = False
        mock_area_manager.get_area = Mock(return_value=mock_area)

        candidate = 45.0
        result = apply_pid_adjustment(mock_area_manager, "test_area", candidate)

        assert result == candidate

    def test_inactive_mode_returns_original_candidate(self, mock_area, mock_area_manager):
        """Test inactive mode returns original candidate."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home", "comfort"]
        mock_area.preset_mode = "away"  # Not in active modes
        mock_area_manager.get_area = Mock(return_value=mock_area)

        candidate = 45.0
        result = apply_pid_adjustment(mock_area_manager, "test_area", candidate)

        assert result == candidate

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_active_applies_adjustment(self, mock_area, mock_area_manager):
        """Test PID active applies adjustment to candidate."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area_manager.get_area = Mock(return_value=mock_area)

        candidate = 45.0
        result = apply_pid_adjustment(mock_area_manager, "test_area", candidate)

        # Result should be different from candidate (PID adjustment applied)
        # With error = 21.0 - 20.0 = 1.0, PID should add some adjustment
        assert result != candidate

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_creates_controller_on_first_call(self, mock_area, mock_area_manager):
        """Test PID controller created on first call."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area_manager.get_area = Mock(return_value=mock_area)

        assert "test_area" not in _pids

        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)

        assert "test_area" in _pids
        assert isinstance(_pids["test_area"], PID)

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_reuses_existing_controller(self, mock_area, mock_area_manager):
        """Test PID reuses existing controller on subsequent calls."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area_manager.get_area = Mock(return_value=mock_area)

        # First call creates controller
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        first_pid = _pids["test_area"]

        # Second call should reuse
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        second_pid = _pids["test_area"]

        assert first_pid is second_pid

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_clears_state_when_disabled(self, mock_area, mock_area_manager):
        """Test PID state cleared when disabled."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area_manager.get_area = Mock(return_value=mock_area)

        # Create PID
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        assert "test_area" in _pids

        # Disable PID
        mock_area.pid_enabled = False
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)

        # Should be cleared
        assert "test_area" not in _pids

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_clears_state_when_mode_changes(self, mock_area, mock_area_manager):
        """Test PID state cleared when mode not in active modes."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area_manager.get_area = Mock(return_value=mock_area)

        # Create PID in home mode
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        assert "test_area" in _pids

        # Change to away mode (not in active modes)
        mock_area.preset_mode = "away"
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)

        # Should be cleared
        assert "test_area" not in _pids

    def test_none_area_returns_original_candidate(self, mock_area_manager):
        """Test None area returns original candidate."""
        mock_area_manager.get_area = Mock(return_value=None)

        candidate = 45.0
        result = apply_pid_adjustment(mock_area_manager, "nonexistent", candidate)

        assert result == candidate

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_none_current_temperature_returns_original(self, mock_area, mock_area_manager):
        """Test None current temperature returns original candidate."""
        mock_area.current_temperature = None
        mock_area_manager.get_area = Mock(return_value=mock_area)

        candidate = 45.0
        result = apply_pid_adjustment(mock_area_manager, "test_area", candidate)

        assert result == candidate

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_uses_area_heating_type(self, mock_area, mock_area_manager):
        """Test PID controller uses area's heating type."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area.heating_type = "floor_heating"
        mock_area_manager.get_area = Mock(return_value=mock_area)

        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)

        pid = _pids["test_area"]
        assert pid.heating_system == "floor_heating"
        # Floor heating should have 50.0 integral limit
        assert pid.integral_limit == 50.0

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_uses_automatic_gains_setting(self, mock_area, mock_area_manager):
        """Test PID controller respects automatic_gains setting."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area.pid_automatic_gains = False
        mock_area_manager.get_area = Mock(return_value=mock_area)

        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)

        pid = _pids["test_area"]
        assert pid.automatic_gains is False

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_uses_area_heating_curve_coefficient(self, mock_area, mock_area_manager):
        """Test PID uses area heating curve coefficient."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area.heating_curve_coefficient = 2.5
        mock_area_manager.get_area = Mock(return_value=mock_area)

        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)

        pid = _pids["test_area"]
        assert pid._coefficient == 2.5

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_uses_default_coefficient_when_none(self, mock_area, mock_area_manager):
        """Test PID uses default coefficient when area's is None."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        mock_area.heating_curve_coefficient = None
        mock_area_manager.default_heating_curve_coefficient = 1.8
        mock_area_manager.get_area = Mock(return_value=mock_area)

        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)

        pid = _pids["test_area"]
        assert pid._coefficient == 1.8


class TestPIDIntegration:
    """Integration tests for PID controller manager."""

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_schedule_mode_activates_pid(self, mock_area, mock_area_manager):
        """Test PID activates when schedule is active."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["schedule"]
        mock_area.preset_mode = "none"
        mock_area.schedule_manager.is_schedule_active.return_value = True
        mock_area_manager.get_area = Mock(return_value=mock_area)

        candidate = 45.0
        result = apply_pid_adjustment(mock_area_manager, "test_area", candidate)

        # PID should be active
        assert "test_area" in _pids
        assert result != candidate  # Adjustment applied

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_multiple_mode_transitions(self, mock_area, mock_area_manager):
        """Test PID handles multiple mode transitions."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home", "comfort"]
        mock_area_manager.get_area = Mock(return_value=mock_area)

        # Start in home mode (active)
        mock_area.preset_mode = "home"
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        assert "test_area" in _pids

        # Switch to away mode (inactive) - should clear
        mock_area.preset_mode = "away"
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        assert "test_area" not in _pids

        # Switch to comfort mode (active) - should recreate
        mock_area.preset_mode = "comfort"
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        assert "test_area" in _pids

        # Disable PID - should clear
        mock_area.pid_enabled = False
        apply_pid_adjustment(mock_area_manager, "test_area", 45.0)
        assert "test_area" not in _pids

    @patch("smart_heating.climate.controllers.heating_curve_manager._heating_curves", {})
    def test_pid_adjustment_bounded(self, mock_area, mock_area_manager):
        """Test PID adjustment is always bounded."""
        mock_area.pid_enabled = True
        mock_area.pid_active_modes = ["home"]
        mock_area.preset_mode = "home"
        # Large temperature error
        mock_area.target_temperature = 30.0
        mock_area.current_temperature = 10.0  # 20°C error
        mock_area_manager.get_area = Mock(return_value=mock_area)

        candidate = 50.0
        result = apply_pid_adjustment(mock_area_manager, "test_area", candidate)

        # PID output should be clamped to ±15.0
        # So result should be at most candidate + 15.0
        assert result <= candidate + 15.0
        assert result >= candidate - 15.0
