"""Tests for OpenTherm gateway handler."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from smart_heating.climate.devices.opentherm_handler import OpenThermHandler


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.states = MagicMock()
    hass.data = {}
    return hass


@pytest.fixture
def mock_area_manager():
    """Create mock AreaManager."""
    manager = MagicMock()
    manager.opentherm_gateway_id = "sensor.opentherm_gateway"
    manager.pwm_enabled = False
    manager.advanced_control_enabled = False
    manager.heating_curve_enabled = False
    manager.pid_enabled = False
    return manager


@pytest.fixture
def mock_capability_detector():
    """Create mock capability detector."""
    return MagicMock()


@pytest.fixture
def opentherm_handler(mock_hass, mock_area_manager, mock_capability_detector):
    """Create OpenThermHandler instance."""
    return OpenThermHandler(mock_hass, mock_area_manager, mock_capability_detector)


class TestOpenThermHandler:
    """Test OpenTherm handler operations."""

    @pytest.mark.asyncio
    async def test_set_gateway_setpoint_positive_temperature(self, opentherm_handler, mock_hass):
        """Test setting gateway setpoint with positive temperature."""
        await opentherm_handler._set_gateway_setpoint("gateway1", 55.0)

        mock_hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 55.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_set_gateway_setpoint_zero_temperature(self, opentherm_handler, mock_hass):
        """Test setting gateway setpoint with zero temperature (off)."""
        await opentherm_handler._set_gateway_setpoint("gateway1", 0.0)

        mock_hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 0.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_set_gateway_setpoint_negative_temperature_clamped_to_zero(
        self, opentherm_handler, mock_hass
    ):
        """Test that negative temperature is clamped to 0 before calling service.

        This reproduces the bug where negative temperatures cause:
        "value must be at least 0 for dictionary value @ data['temperature']"
        """
        # Call with negative temperature
        await opentherm_handler._set_gateway_setpoint("gateway1", -5.0)

        # Should be clamped to 0.0, not passed as negative
        mock_hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 0.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_set_gateway_setpoint_high_temperature_clamped_to_90(
        self, opentherm_handler, mock_hass
    ):
        """Test that temperature above 90°C is clamped to 90°C before calling service.

        This reproduces the bug where temperatures above 90°C cause:
        "value must be at most 90 for dictionary value @ data['temperature']"

        Bug context: When heating curve or advanced control calculates a very high
        setpoint (e.g., 95°C), the OpenTherm gateway service rejects it with a
        voluptuous.error.MultipleInvalid exception because the service schema
        enforces a maximum of 90°C.
        """
        # Call with temperature above 90°C
        await opentherm_handler._set_gateway_setpoint("gateway1", 95.0)

        # Should be clamped to 90.0, not passed as 95.0
        mock_hass.services.async_call.assert_called_once_with(
            "opentherm_gw",
            "set_control_setpoint",
            {"gateway_id": "gateway1", "temperature": 90.0},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_apply_pwm_approximation_with_negative_setpoint(
        self, opentherm_handler, mock_hass
    ):
        """Test PWM approximation handles negative boiler_setpoint correctly."""
        # Setup gateway state without modulation support
        gateway_state = MagicMock()
        gateway_state.attributes = {
            "relative_mod_level": None,
            "boiler_water_temp": 50.0,
        }
        mock_hass.states.get.return_value = gateway_state

        heating_types = {"area1": "radiator"}

        # Pass negative setpoint
        result = opentherm_handler._apply_pwm_approximation("gateway1", -10.0, heating_types)

        # Should clamp to 0.0
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_control_gateway_heating_off_calls_with_zero(self, opentherm_handler, mock_hass):
        """Test that turning off gateway uses 0.0 temperature."""
        await opentherm_handler._control_gateway_heating_off("gateway1", None)

        mock_hass.services.async_call.assert_called_once()
        call_args = mock_hass.services.async_call.call_args
        assert call_args.args[2]["temperature"] == 0.0

    def test_calculate_pwm_duty_with_negative_setpoint(self, opentherm_handler):
        """Test PWM duty calculation with negative setpoint."""
        heating_types = {"area1": "radiator"}

        # With radiator: base_offset = 27.2
        # If boiler_setpoint = -5.0 and boiler_temp = 50.0
        # duty = (-5.0 - 27.2) / (50.0 - 27.2) = -32.2 / 22.8 = -1.41
        # After clamping: 0.0
        duty = opentherm_handler._calculate_pwm_duty(-5.0, 50.0, heating_types)

        assert duty == 0.0  # Clamped to minimum

    def test_calculate_pwm_duty_with_very_low_setpoint(self, opentherm_handler):
        """Test PWM duty calculation with setpoint below base offset."""
        heating_types = {"area1": "floor_heating"}

        # With floor heating: base_offset = 20.0
        # If boiler_setpoint = 15.0 and boiler_temp = 45.0
        # duty = (15.0 - 20.0) / (45.0 - 20.0) = -5.0 / 25.0 = -0.2
        # After clamping: 0.0
        duty = opentherm_handler._calculate_pwm_duty(15.0, 45.0, heating_types)

        assert duty == 0.0  # Clamped to minimum
