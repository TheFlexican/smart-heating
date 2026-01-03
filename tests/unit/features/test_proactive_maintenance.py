"""Tests for ProactiveMaintenanceHandler."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.features.proactive_maintenance import (
    ProactiveMaintenanceHandler,
    ProactiveMaintenanceResult,
)


class TestProactiveMaintenanceResult:
    """Test ProactiveMaintenanceResult dataclass."""

    def test_result_creation_minimal(self):
        """Test creating a result with minimal fields."""
        result = ProactiveMaintenanceResult(
            should_heat=False,
            reason="Test reason",
        )
        assert result.should_heat is False
        assert result.reason == "Test reason"
        assert result.time_to_threshold is None
        assert result.predicted_heating_time is None
        assert result.current_temp is None
        assert result.target_temp is None
        assert result.trend is None

    def test_result_creation_full(self):
        """Test creating a result with all fields."""
        result = ProactiveMaintenanceResult(
            should_heat=True,
            reason="Proactive heating triggered",
            time_to_threshold=30.0,
            predicted_heating_time=25,
            current_temp=19.8,
            target_temp=20.0,
            trend=-0.3,
        )
        assert result.should_heat is True
        assert result.reason == "Proactive heating triggered"
        assert result.time_to_threshold == 30.0
        assert result.predicted_heating_time == 25
        assert result.current_temp == 19.8
        assert result.target_temp == 20.0
        assert result.trend == -0.3


class TestProactiveMaintenanceHandler:
    """Test ProactiveMaintenanceHandler functionality."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = MagicMock()
        return hass

    @pytest.fixture
    def mock_temperature_tracker(self):
        """Create mock temperature tracker."""
        tracker = MagicMock()
        tracker.get_latest_temperature = MagicMock(return_value=19.8)
        tracker.get_trend = MagicMock(return_value=-0.3)
        tracker.predict_time_to_temperature = MagicMock(return_value=30.0)
        return tracker

    @pytest.fixture
    def mock_learning_engine(self):
        """Create mock learning engine."""
        engine = MagicMock()
        engine.async_predict_heating_time = AsyncMock(return_value=25)
        engine.async_get_average_cooling_rate = AsyncMock(return_value=-0.2)
        return engine

    @pytest.fixture
    def mock_area_logger(self):
        """Create mock area logger."""
        logger = MagicMock()
        logger.log_event = MagicMock()
        return logger

    @pytest.fixture
    def mock_boost_manager(self):
        """Create mock boost manager."""
        manager = MagicMock()
        manager.proactive_maintenance_enabled = True
        manager.proactive_maintenance_active = False
        manager.proactive_maintenance_sensitivity = 1.0
        manager.proactive_maintenance_min_trend = -0.1
        manager.proactive_maintenance_margin_minutes = 5
        manager.proactive_maintenance_cooldown_minutes = 10
        manager.is_proactive_cooldown_active = MagicMock(return_value=False)
        manager.get_effective_margin_minutes = MagicMock(return_value=5)
        return manager

    @pytest.fixture
    def mock_area(self, mock_boost_manager):
        """Create mock area."""
        area = MagicMock()
        area.area_id = "living_room"
        area.name = "Living Room"
        area.current_temperature = 19.8
        area.target_temperature = 20.0
        area.boost_manager = mock_boost_manager
        area.hysteresis_override = None  # Explicitly set to None so _get_hysteresis uses default
        return area

    @pytest.fixture
    def handler(self, mock_hass, mock_temperature_tracker, mock_learning_engine, mock_area_logger):
        """Create handler instance."""
        return ProactiveMaintenanceHandler(
            hass=mock_hass,
            temperature_tracker=mock_temperature_tracker,
            learning_engine=mock_learning_engine,
            area_logger=mock_area_logger,
            default_hysteresis=0.5,
        )

    @pytest.mark.asyncio
    async def test_check_area_disabled(self, handler, mock_area):
        """Test check when proactive maintenance is disabled."""
        mock_area.boost_manager.proactive_maintenance_enabled = False

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "disabled" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_already_active_continue(
        self, handler, mock_area, mock_temperature_tracker
    ):
        """Test continuing proactive heating when active and below target."""
        mock_area.boost_manager.proactive_maintenance_active = True
        mock_temperature_tracker.get_latest_temperature.return_value = 19.5  # Below target

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is True
        assert "continuing" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_already_active_target_reached(
        self, handler, mock_area, mock_temperature_tracker
    ):
        """Test stopping proactive heating when target is reached."""
        mock_area.boost_manager.proactive_maintenance_active = True
        mock_area.current_temperature = 20.0  # At target
        mock_temperature_tracker.get_latest_temperature.return_value = 20.0  # At target

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "target" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_cooldown_active(self, handler, mock_area):
        """Test check when cooldown is active."""
        mock_area.boost_manager.is_proactive_cooldown_active.return_value = True

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "cooldown" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_no_temperature_data(
        self, handler, mock_area, mock_temperature_tracker
    ):
        """Test check when no temperature data available."""
        mock_area.current_temperature = None
        mock_temperature_tracker.get_latest_temperature.return_value = None

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "no temperature" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_no_target_temperature(self, handler, mock_area):
        """Test check when no target temperature set."""
        mock_area.target_temperature = None

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "no target" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_no_trend_data(self, handler, mock_area, mock_temperature_tracker):
        """Test check when no trend data available."""
        mock_temperature_tracker.get_trend.return_value = None

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "no trend" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_temperature_rising(
        self, handler, mock_area, mock_temperature_tracker
    ):
        """Test check when temperature is rising (positive trend)."""
        mock_temperature_tracker.get_trend.return_value = 0.5  # Rising

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "stable or rising" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_temperature_stable(
        self, handler, mock_area, mock_temperature_tracker
    ):
        """Test check when temperature is stable (trend above min_trend)."""
        mock_temperature_tracker.get_trend.return_value = (
            -0.05
        )  # Slightly falling but above threshold

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "stable or rising" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_already_below_threshold(
        self, handler, mock_area, mock_temperature_tracker
    ):
        """Test check when temperature is already below hysteresis threshold."""
        mock_area.current_temperature = 19.0  # Below 19.5 threshold
        mock_temperature_tracker.get_latest_temperature.return_value = 19.0  # Below 19.5 threshold
        mock_temperature_tracker.get_trend.return_value = -0.3

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "already below" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_cannot_predict_time(
        self, handler, mock_area, mock_temperature_tracker
    ):
        """Test check when time to threshold cannot be predicted."""
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = None

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "cannot predict" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_no_learning_data(
        self, handler, mock_area, mock_temperature_tracker, mock_learning_engine
    ):
        """Test check when no learning data available."""
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0
        mock_learning_engine.async_predict_heating_time.return_value = None
        mock_learning_engine.async_get_average_cooling_rate.return_value = None

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "insufficient learning" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_proactive_heating_triggered(
        self, handler, mock_area, mock_temperature_tracker, mock_learning_engine
    ):
        """Test check when proactive heating should be triggered."""
        # Set up scenario: temp falling, 30 min to threshold, 25 min heating + 5 margin >= 30
        mock_temperature_tracker.get_latest_temperature.return_value = 19.8
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0
        mock_learning_engine.async_predict_heating_time.return_value = 25

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is True
        assert "triggered" in result.reason.lower()
        assert result.time_to_threshold == 30.0
        assert result.predicted_heating_time == 25
        assert result.current_temp == 19.8
        assert result.target_temp == 20.0
        assert result.trend == -0.3

    @pytest.mark.asyncio
    async def test_check_area_not_yet_time_to_heat(
        self, handler, mock_area, mock_temperature_tracker, mock_learning_engine
    ):
        """Test check when it's not yet time to start heating."""
        # Set up scenario: temp falling slowly, 120 min to threshold, 25 min heating + 5 margin < 120
        mock_temperature_tracker.get_latest_temperature.return_value = 19.9
        mock_temperature_tracker.get_trend.return_value = -0.15
        mock_temperature_tracker.predict_time_to_temperature.return_value = 120.0
        mock_learning_engine.async_predict_heating_time.return_value = 25

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "not yet" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_check_area_uses_cooling_rate_fallback(
        self, handler, mock_area, mock_temperature_tracker, mock_learning_engine
    ):
        """Test using cooling rate as fallback when no heating data."""
        mock_temperature_tracker.get_latest_temperature.return_value = 19.8
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0
        mock_learning_engine.async_predict_heating_time.return_value = None
        mock_learning_engine.async_get_average_cooling_rate.return_value = -0.2

        result = await handler.async_check_area(mock_area)

        # With cooling rate of -0.2°C/h, heating rate estimate is 0.4°C/h
        # To heat 0.2°C (19.8 to 20.0), it would take 0.2/0.4 = 0.5 hours = 30 min
        # 30 min predicted + 5 min margin >= 30 min to threshold
        assert result.should_heat is True

    @pytest.mark.asyncio
    async def test_check_area_sensitivity_adjustment(
        self, handler, mock_area, mock_temperature_tracker, mock_learning_engine
    ):
        """Test that sensitivity adjusts predicted heating time."""
        # Lower sensitivity = less aggressive (heating time multiplied by less)
        mock_area.boost_manager.proactive_maintenance_sensitivity = 0.5
        mock_temperature_tracker.get_latest_temperature.return_value = 19.8
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0
        mock_learning_engine.async_predict_heating_time.return_value = 40  # 40 * 0.5 + 5 = 25 < 30

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False

    @pytest.mark.asyncio
    async def test_check_area_floor_heating_margin(
        self, handler, mock_area, mock_temperature_tracker, mock_learning_engine
    ):
        """Test that floor heating uses larger margin."""
        mock_area.boost_manager.get_effective_margin_minutes.return_value = (
            15  # Floor heating margin
        )
        mock_temperature_tracker.get_latest_temperature.return_value = 19.8
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0
        mock_learning_engine.async_predict_heating_time.return_value = 10  # 10 + 15 = 25 < 30

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False

    @pytest.mark.asyncio
    async def test_check_area_logs_event_on_trigger(
        self, handler, mock_area, mock_temperature_tracker, mock_learning_engine, mock_area_logger
    ):
        """Test that event is logged when proactive heating is triggered."""
        mock_area.current_temperature = 19.8
        mock_temperature_tracker.get_latest_temperature.return_value = 19.8
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0
        mock_learning_engine.async_predict_heating_time.return_value = 25

        await handler.async_check_area(mock_area)

        # Verify that log_event was called (multiple times during the check process)
        assert mock_area_logger.log_event.called
        # Verify the final call indicates proactive heating was triggered
        call_args = mock_area_logger.log_event.call_args
        assert call_args[0][0] == "living_room"  # area_id
        assert call_args[0][1] == "proactive_maintenance"  # event_type
        assert "heating started" in call_args[0][2].lower()  # message indicates heating started

    @pytest.mark.asyncio
    async def test_handler_without_learning_engine(
        self, mock_hass, mock_temperature_tracker, mock_area_logger, mock_area
    ):
        """Test handler without learning engine."""
        handler = ProactiveMaintenanceHandler(
            hass=mock_hass,
            temperature_tracker=mock_temperature_tracker,
            learning_engine=None,  # No learning engine
            area_logger=mock_area_logger,
        )

        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0

        result = await handler.async_check_area(mock_area)

        assert result.should_heat is False
        assert "insufficient learning" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_handler_without_area_logger(
        self, mock_hass, mock_temperature_tracker, mock_learning_engine, mock_area
    ):
        """Test handler without area logger."""
        handler = ProactiveMaintenanceHandler(
            hass=mock_hass,
            temperature_tracker=mock_temperature_tracker,
            learning_engine=mock_learning_engine,
            area_logger=None,  # No logger
        )

        mock_temperature_tracker.get_latest_temperature.return_value = 19.8
        mock_temperature_tracker.get_trend.return_value = -0.3
        mock_temperature_tracker.predict_time_to_temperature.return_value = 30.0
        mock_learning_engine.async_predict_heating_time.return_value = 25

        # Should not raise even without logger
        result = await handler.async_check_area(mock_area)
        assert result.should_heat is True


class TestProactiveMaintenanceHandlerHysteresis:
    """Test hysteresis handling in ProactiveMaintenanceHandler."""

    @pytest.fixture
    def handler(self):
        """Create handler with default hysteresis."""
        return ProactiveMaintenanceHandler(
            hass=MagicMock(),
            temperature_tracker=MagicMock(),
            learning_engine=None,
            default_hysteresis=0.5,
        )

    def test_get_hysteresis_default(self, handler):
        """Test getting default hysteresis."""
        area = MagicMock()
        area.hysteresis_override = None

        result = handler._get_hysteresis(area)
        assert result == 0.5

    def test_get_hysteresis_override(self, handler):
        """Test getting overridden hysteresis."""
        area = MagicMock()
        area.hysteresis_override = 0.3

        result = handler._get_hysteresis(area)
        assert result == 0.3

    def test_get_hysteresis_no_attribute(self, handler):
        """Test getting hysteresis when area has no override attribute."""
        area = MagicMock(spec=[])  # No hysteresis_override attribute

        result = handler._get_hysteresis(area)
        assert result == 0.5
