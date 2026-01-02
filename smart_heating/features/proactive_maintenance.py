"""Proactive temperature maintenance for Smart Heating.

This module provides proactive temperature maintenance by predicting
temperature drops and starting heating before the hysteresis threshold
is reached, maintaining constant room temperature.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant

if TYPE_CHECKING:
    from ..area_logger import AreaLogger
    from ..core.coordination.temperature_tracker import TemperatureTracker
    from ..features.learning_engine import LearningEngine
    from ..models.area import Area

_LOGGER = logging.getLogger(__name__)


@dataclass
class ProactiveMaintenanceResult:
    """Result of proactive maintenance check."""

    should_heat: bool
    reason: str
    time_to_threshold: float | None = None  # Minutes until hysteresis threshold
    predicted_heating_time: int | None = None  # Minutes to heat back up
    current_temp: float | None = None
    target_temp: float | None = None
    trend: float | None = None  # Temperature trend in C/hour


class ProactiveMaintenanceHandler:
    """Handler for proactive temperature maintenance.

    This handler monitors temperature trends during active schedules and
    predicts when temperature will drop below the hysteresis threshold.
    If predicted heating time exceeds time until threshold, it triggers
    proactive heating to maintain constant temperature.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        temperature_tracker: "TemperatureTracker",
        learning_engine: "LearningEngine | None",
        area_logger: "AreaLogger | None" = None,
        default_hysteresis: float = 0.5,
    ) -> None:
        """Initialize proactive maintenance handler.

        Args:
            hass: Home Assistant instance
            temperature_tracker: Temperature tracker for trend analysis
            learning_engine: Learning engine for heating time predictions
            area_logger: Optional area logger for event logging
            default_hysteresis: Default hysteresis value if not set on area
        """
        self.hass = hass
        self.temperature_tracker = temperature_tracker
        self.learning_engine = learning_engine
        self.area_logger = area_logger
        self.default_hysteresis = default_hysteresis

        _LOGGER.debug("ProactiveMaintenanceHandler initialized")

    def _validate_temperatures(
        self,
        area: "Area",
        area_id: str,
    ) -> tuple[float | None, float | None]:
        """Validate and get current and target temperatures.

        Returns:
            Tuple of (current_temp, target_temp)
        """
        current_temp = self.temperature_tracker.get_latest_temperature(area_id)
        target_temp = area.target_temperature
        return current_temp, target_temp

    def _check_temperature_trend(
        self,
        area: "Area",
        area_id: str,
        current_temp: float,
        target_temp: float,
    ) -> tuple[float | None, ProactiveMaintenanceResult | None]:
        """Check temperature trend and validate it meets threshold.

        Returns:
            Tuple of (trend, early_exit_result). If early_exit_result is not None,
            return it immediately to exit the check.
        """
        trend = self.temperature_tracker.get_trend(area_id)
        if trend is None:
            return None, ProactiveMaintenanceResult(
                should_heat=False,
                reason="No trend data available",
                current_temp=current_temp,
                target_temp=target_temp,
            )

        min_trend = area.boost_manager.proactive_maintenance_min_trend
        if trend >= min_trend:  # min_trend is negative (e.g., -0.1)
            return trend, ProactiveMaintenanceResult(
                should_heat=False,
                reason=f"Temperature stable or rising (trend: {trend:.2f}C/h)",
                current_temp=current_temp,
                target_temp=target_temp,
                trend=trend,
            )

        return trend, None

    def _check_hysteresis_threshold(
        self,
        area: "Area",
        current_temp: float,
        target_temp: float,
        trend: float,
    ) -> tuple[float, ProactiveMaintenanceResult | None]:
        """Check if temperature is below hysteresis threshold.

        Returns:
            Tuple of (threshold_temp, early_exit_result). If early_exit_result is not None,
            return it immediately.
        """
        hysteresis = self._get_hysteresis(area)
        threshold_temp = target_temp - hysteresis

        if current_temp <= threshold_temp:
            return threshold_temp, ProactiveMaintenanceResult(
                should_heat=False,
                reason="Already below hysteresis threshold",
                current_temp=current_temp,
                target_temp=target_temp,
                trend=trend,
            )

        return threshold_temp, None

    async def _calculate_heating_decision(
        self,
        area: "Area",
        area_id: str,
        current_temp: float,
        target_temp: float,
        trend: float,
        threshold_temp: float,
        time_to_threshold: float,
    ) -> ProactiveMaintenanceResult:
        """Calculate if proactive heating should start based on predictions.

        Returns:
            ProactiveMaintenanceResult with final decision
        """
        # Get predicted heating time
        predicted_heating_time = await self._get_predicted_heating_time(
            area_id, current_temp, target_temp
        )
        if predicted_heating_time is None:
            predicted_heating_time = await self._estimate_heating_from_cooling(
                area_id, current_temp, target_temp
            )

        if predicted_heating_time is None:
            return ProactiveMaintenanceResult(
                should_heat=False,
                reason="Insufficient learning data for prediction",
                current_temp=current_temp,
                target_temp=target_temp,
                trend=trend,
                time_to_threshold=time_to_threshold,
            )

        # Apply sensitivity and margin
        margin = area.boost_manager.get_effective_margin_minutes()
        sensitivity = area.boost_manager.proactive_maintenance_sensitivity
        adjusted_heating_time = predicted_heating_time * sensitivity + margin
        should_heat = adjusted_heating_time >= time_to_threshold

        if should_heat:
            self._log_proactive_heating_start(
                area_id,
                trend,
                time_to_threshold,
                adjusted_heating_time,
                predicted_heating_time,
                margin,
                sensitivity,
                current_temp,
                target_temp,
                threshold_temp,
            )

        return ProactiveMaintenanceResult(
            should_heat=should_heat,
            reason="Proactive heating triggered" if should_heat else "Not yet time to heat",
            time_to_threshold=time_to_threshold,
            predicted_heating_time=predicted_heating_time,
            current_temp=current_temp,
            target_temp=target_temp,
            trend=trend,
        )

    def _log_proactive_heating_start(
        self,
        area_id: str,
        trend: float,
        time_to_threshold: float,
        adjusted_heating_time: float,
        predicted_heating_time: float,
        margin: float,
        sensitivity: float,
        current_temp: float,
        target_temp: float,
        threshold_temp: float,
    ) -> None:
        """Log proactive heating start event."""
        _LOGGER.info(
            "Proactive heating triggered for %s: trend=%.2fC/h, "
            "time_to_threshold=%.1f min, predicted_heating=%.1f min (adjusted)",
            area_id,
            trend,
            time_to_threshold,
            adjusted_heating_time,
        )

        if self.area_logger:
            self.area_logger.log_event(
                area_id,
                "proactive_maintenance",
                f"Proactive heating started - predicted {predicted_heating_time} min to maintain {target_temp:.1f}C",
                {
                    "trigger": "falling_trend",
                    "trend": trend,
                    "time_to_threshold": time_to_threshold,
                    "predicted_heating_time": predicted_heating_time,
                    "adjusted_heating_time": adjusted_heating_time,
                    "margin": margin,
                    "sensitivity": sensitivity,
                    "current_temp": current_temp,
                    "target_temp": target_temp,
                    "threshold_temp": threshold_temp,
                },
            )

    async def async_check_area(
        self,
        area: "Area",
        current_time: datetime | None = None,
    ) -> ProactiveMaintenanceResult:
        """Check if proactive maintenance is needed for an area.

        Args:
            area: Area to check
            current_time: Current time (defaults to now)

        Returns:
            ProactiveMaintenanceResult with decision and details
        """
        if current_time is None:
            current_time = datetime.now()

        area_id = area.area_id

        # Check if feature is enabled
        if not area.boost_manager.proactive_maintenance_enabled:
            return ProactiveMaintenanceResult(
                should_heat=False,
                reason="Proactive maintenance disabled",
            )

        # Check if already in proactive heating
        if area.boost_manager.proactive_maintenance_active:
            return self._check_continue_proactive_heating(area)

        # Check cooldown period
        if area.boost_manager.is_proactive_cooldown_active(current_time):
            return ProactiveMaintenanceResult(
                should_heat=False,
                reason="Cooldown period active",
            )

        # Validate temperatures
        current_temp, target_temp = self._validate_temperatures(area, area_id)
        if current_temp is None:
            return ProactiveMaintenanceResult(
                should_heat=False,
                reason="No temperature data available",
            )
        if target_temp is None:
            return ProactiveMaintenanceResult(
                should_heat=False,
                reason="No target temperature set",
            )

        # Check temperature trend
        trend, early_exit = self._check_temperature_trend(area, area_id, current_temp, target_temp)
        if early_exit:
            return early_exit

        # Check hysteresis threshold
        threshold_temp, early_exit = self._check_hysteresis_threshold(
            area, current_temp, target_temp, trend
        )
        if early_exit:
            return early_exit

        # Calculate time until threshold is reached
        time_to_threshold = self.temperature_tracker.predict_time_to_temperature(
            area_id, threshold_temp
        )
        if time_to_threshold is None or time_to_threshold <= 0:
            return ProactiveMaintenanceResult(
                should_heat=False,
                reason="Cannot predict time to threshold",
                current_temp=current_temp,
                target_temp=target_temp,
                trend=trend,
            )

        # Make final heating decision
        return await self._calculate_heating_decision(
            area,
            area_id,
            current_temp,
            target_temp,
            trend,
            threshold_temp,
            time_to_threshold,
        )

    def _check_continue_proactive_heating(
        self,
        area: "Area",
    ) -> ProactiveMaintenanceResult:
        """Check if proactive heating should continue.

        Args:
            area: Area being checked

        Returns:
            ProactiveMaintenanceResult
        """
        area_id = area.area_id
        current_temp = self.temperature_tracker.get_latest_temperature(area_id)
        target_temp = area.target_temperature

        if current_temp is None or target_temp is None:
            return ProactiveMaintenanceResult(
                should_heat=True,  # Continue if we can't determine state
                reason="Continuing proactive heating (no temp data)",
            )

        # Stop proactive heating if target reached
        if current_temp >= target_temp:
            _LOGGER.info(
                "Proactive heating complete for %s: target %.1fC reached (current: %.1fC)",
                area_id,
                target_temp,
                current_temp,
            )

            if self.area_logger:
                self.area_logger.log_event(
                    area_id,
                    "proactive_maintenance",
                    f"Proactive heating ended - target {target_temp:.1f}C reached",
                    {
                        "reason": "target_reached",
                        "current_temp": current_temp,
                        "target_temp": target_temp,
                    },
                )

            return ProactiveMaintenanceResult(
                should_heat=False,
                reason="Target temperature reached",
                current_temp=current_temp,
                target_temp=target_temp,
            )

        # Continue proactive heating
        return ProactiveMaintenanceResult(
            should_heat=True,
            reason="Continuing proactive heating",
            current_temp=current_temp,
            target_temp=target_temp,
        )

    async def _get_predicted_heating_time(
        self,
        area_id: str,
        current_temp: float,
        target_temp: float,
    ) -> int | None:
        """Get predicted heating time from learning engine.

        Args:
            area_id: Area identifier
            current_temp: Current temperature
            target_temp: Target temperature

        Returns:
            Predicted minutes or None
        """
        if self.learning_engine is None:
            return None

        return await self.learning_engine.async_predict_heating_time(
            area_id, current_temp, target_temp
        )

    async def _estimate_heating_from_cooling(
        self,
        area_id: str,
        current_temp: float,
        target_temp: float,
    ) -> int | None:
        """Estimate heating time based on cooling rate.

        Uses the inverse of cooling rate as a rough heating estimate.
        Less accurate than actual heating data but better than nothing.

        Args:
            area_id: Area identifier
            current_temp: Current temperature
            target_temp: Target temperature

        Returns:
            Estimated minutes or None
        """
        if self.learning_engine is None:
            return None

        cooling_rate = await self.learning_engine.async_get_average_cooling_rate(area_id)
        if cooling_rate is None:
            return None

        # Heating is typically 2-3x faster than cooling (active vs passive)
        # Use conservative estimate of 2x
        heating_rate = abs(cooling_rate) * 2  # C/hour

        temp_diff = target_temp - current_temp
        if temp_diff <= 0 or heating_rate <= 0:
            return 0

        hours_to_heat = temp_diff / heating_rate
        return int(hours_to_heat * 60)

    def _get_hysteresis(self, area: "Area") -> float:
        """Get hysteresis value for area.

        Args:
            area: Area to get hysteresis for

        Returns:
            Hysteresis value in degrees Celsius
        """
        if hasattr(area, "hysteresis_override") and area.hysteresis_override is not None:
            return area.hysteresis_override
        return self.default_hysteresis
