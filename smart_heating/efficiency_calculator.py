"""Heating Efficiency Calculator for Smart Heating."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class EfficiencyCalculator:
    """Calculate heating efficiency metrics for areas."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize efficiency calculator.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    async def calculate_area_efficiency(
        self,
        area_id: str,
        period: str = "day",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Calculate efficiency metrics for an area.

        Args:
            area_id: Area ID to calculate efficiency for
            period: Time period - "day", "week", "month"
            start_time: Optional custom start time
            end_time: Optional custom end time

        Returns:
            Dictionary containing efficiency metrics
        """
        # Determine time range
        if start_time and end_time:
            start = start_time
            end = end_time
        else:
            end = dt_util.now()
            if period == "day":
                start = end - timedelta(days=1)
            elif period == "week":
                start = end - timedelta(weeks=1)
            elif period == "month":
                start = end - timedelta(days=30)
            else:
                start = end - timedelta(days=1)

        # Get climate entity for this area
        climate_entity_id = f"climate.smart_heating_{area_id}"

        # Fetch historical data
        try:
            states = await self._fetch_states(climate_entity_id, start, end)

            if not states:
                _LOGGER.warning(
                    "No historical data found for %s between %s and %s",
                    climate_entity_id,
                    start,
                    end,
                )
                return self._empty_metrics(area_id, period, start, end)

            # Calculate metrics
            heating_time_percentage = self._calculate_heating_time(states)
            avg_temp_delta = self._calculate_avg_temp_delta(states)
            heating_cycles = self._count_heating_cycles(states)
            temp_stability = self._calculate_temp_stability(states)

            # Calculate overall efficiency score (0-100)
            # Higher score = more efficient
            energy_score = self._calculate_energy_score(
                heating_time_percentage, avg_temp_delta, heating_cycles, len(states)
            )

            return {
                "area_id": area_id,
                "period": period,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "heating_time_percentage": round(heating_time_percentage, 2),
                "average_temperature_delta": round(avg_temp_delta, 2),
                "heating_cycles": heating_cycles,
                "energy_score": round(energy_score, 2),
                "temperature_stability": round(temp_stability, 2),
                "data_points": len(states),
                "recommendations": self._generate_recommendations(
                    energy_score,
                    heating_time_percentage,
                    avg_temp_delta,
                    heating_cycles,
                ),
            }

        except Exception as e:
            _LOGGER.error("Error calculating efficiency for %s: %s", area_id, e)
            return self._empty_metrics(area_id, period, start, end)

    async def _fetch_states(
        self, entity_id: str, start_time: datetime, end_time: datetime
    ) -> list:
        """Fetch historical states for an entity.

        Args:
            entity_id: Entity ID to fetch states for
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of historical states
        """

        # Use recorder executor to avoid blocking
        def _get_states():
            return history.state_changes_during_period(
                self.hass,
                start_time,
                end_time,
                entity_id,
            )

        recorder = get_instance(self.hass)
        state_changes = await recorder.async_add_executor_job(_get_states)

        if entity_id not in state_changes:
            return []

        return state_changes[entity_id]

    def _calculate_heating_time(self, states: list) -> float:
        """Calculate percentage of time heating was active.

        Args:
            states: List of historical states

        Returns:
            Percentage of time heating was on (0-100)
        """
        if not states:
            return 0.0

        heating_count = 0
        total_count = len(states)

        for state in states:
            if state.state == "heating":
                heating_count += 1

        return (heating_count / total_count) * 100 if total_count > 0 else 0.0

    def _calculate_avg_temp_delta(self, states: list) -> float:
        """Calculate average temperature delta (target - current).

        Args:
            states: List of historical states

        Returns:
            Average temperature difference
        """
        if not states:
            return 0.0

        deltas = []

        for state in states:
            try:
                current_temp = float(state.attributes.get("current_temperature", 0))
                target_temp = float(state.attributes.get("temperature", 0))
                delta = target_temp - current_temp
                deltas.append(abs(delta))
            except (ValueError, TypeError):
                continue

        return sum(deltas) / len(deltas) if deltas else 0.0

    def _count_heating_cycles(self, states: list) -> int:
        """Count number of heating on/off cycles.

        Args:
            states: List of historical states

        Returns:
            Number of heating cycles
        """
        if len(states) < 2:
            return 0

        cycles = 0
        prev_heating = states[0].state == "heating"

        for state in states[1:]:
            current_heating = state.state == "heating"
            if current_heating and not prev_heating:
                cycles += 1
            prev_heating = current_heating

        return cycles

    def _calculate_temp_stability(self, states: list) -> float:
        """Calculate temperature stability (lower = more stable).

        Uses standard deviation of temperature differences.

        Args:
            states: List of historical states

        Returns:
            Temperature stability metric
        """
        if not states:
            return 0.0

        temps = []
        for state in states:
            try:
                current_temp = float(state.attributes.get("current_temperature", 0))
                temps.append(current_temp)
            except (ValueError, TypeError):
                continue

        if len(temps) < 2:
            return 0.0

        # Calculate standard deviation
        mean = sum(temps) / len(temps)
        variance = sum((t - mean) ** 2 for t in temps) / len(temps)
        std_dev = variance**0.5

        return std_dev

    def _calculate_energy_score(
        self,
        heating_time_pct: float,
        avg_temp_delta: float,
        cycles: int,
        data_points: int,
    ) -> float:
        """Calculate overall energy efficiency score (0-100).

        Higher score = more efficient heating.

        Args:
            heating_time_pct: Percentage of time heating was on
            avg_temp_delta: Average temperature difference
            cycles: Number of heating cycles
            data_points: Total number of data points

        Returns:
            Efficiency score (0-100)
        """
        # Start with perfect score
        score = 100.0

        # Penalize excessive heating time (over 50% is inefficient)
        if heating_time_pct > 50:
            score -= (heating_time_pct - 50) * 0.5

        # Penalize large temperature deltas (over 1°C is inefficient)
        if avg_temp_delta > 1.0:
            score -= (avg_temp_delta - 1.0) * 10

        # Penalize excessive cycling (more than 1 cycle per hour is inefficient)
        hours = data_points / 120  # Assuming data points every 30 seconds
        cycles_per_hour = cycles / hours if hours > 0 else 0
        if cycles_per_hour > 1:
            score -= (cycles_per_hour - 1) * 5

        # Clamp to 0-100 range
        return max(0.0, min(100.0, score))

    def _generate_recommendations(
        self,
        energy_score: float,
        heating_time_pct: float,
        avg_temp_delta: float,
        cycles: int,
    ) -> list[str]:
        """Generate recommendations based on efficiency metrics.

        Args:
            energy_score: Overall efficiency score
            heating_time_pct: Percentage of time heating
            avg_temp_delta: Average temperature delta
            cycles: Number of heating cycles

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if energy_score < 50:
            recommendations.append(
                "Low efficiency score detected. Consider checking insulation and window seals."
            )

        if heating_time_pct > 70:
            recommendations.append(
                "Heating is on more than 70% of the time. Consider lowering target temperature or improving insulation."
            )

        if avg_temp_delta > 2.0:
            recommendations.append(
                "Large temperature difference detected. Area may be under-heated or poorly insulated."
            )

        if cycles > 20:
            recommendations.append(
                "Many heating cycles detected. Consider increasing hysteresis value to reduce wear on equipment."
            )

        if not recommendations:
            recommendations.append("Heating efficiency is good. No issues detected.")

        return recommendations

    def _empty_metrics(
        self, area_id: str, period: str, start: datetime, end: datetime
    ) -> dict[str, Any]:
        """Return empty metrics when no data is available.

        Args:
            area_id: Area ID
            period: Time period
            start: Start time
            end: End time

        Returns:
            Empty metrics dictionary
        """
        return {
            "area_id": area_id,
            "period": period,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "heating_time_percentage": 0.0,
            "average_temperature_delta": 0.0,
            "heating_cycles": 0,
            "energy_score": 0.0,
            "temperature_stability": 0.0,
            "data_points": 0,
            "recommendations": ["No data available for this period."],
        }

    async def calculate_all_areas_efficiency(
        self, area_manager, period: str = "day"
    ) -> list[dict[str, Any]]:
        """Calculate efficiency for all areas.

        Args:
            area_manager: AreaManager instance
            period: Time period to calculate

        Returns:
            List of efficiency metrics for all areas
        """
        results = []

        all_areas = area_manager.get_all_areas()
        for area_id, area in all_areas.items():
            if not area.enabled:
                continue

            metrics = await self.calculate_area_efficiency(area_id, period)
            results.append(metrics)

        # Sort by energy score (worst first)
        results.sort(key=lambda x: x["energy_score"])

        return results
