"""Historical Comparison Engine for Smart Heating."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .efficiency_calculator import EfficiencyCalculator

_LOGGER = logging.getLogger(__name__)


class ComparisonEngine:
    """Compare heating performance across different time periods."""

    def __init__(self, hass: HomeAssistant, efficiency_calculator: EfficiencyCalculator) -> None:
        """Initialize comparison engine.

        Args:
            hass: Home Assistant instance
            efficiency_calculator: Efficiency calculator instance
        """
        self.hass = hass
        self.efficiency_calculator = efficiency_calculator

    async def compare_periods(
        self,
        area_id: str,
        comparison_type: str,
        offset: int = 1,
    ) -> dict[str, Any]:
        """Compare current period to previous period.

        Args:
            area_id: Area ID to compare
            comparison_type: Type of comparison - "day", "week", "month", "year"
            offset: How many periods back to compare (default: 1)

        Returns:
            Dictionary containing comparison data
        """
        now = dt_util.now()

        # Determine time ranges
        if comparison_type == "day":
            period_a_end = now
            period_a_start = now - timedelta(days=1)
            period_b_end = now - timedelta(days=offset)
            period_b_start = period_b_end - timedelta(days=1)
            period_name = f"Last {offset} day(s)"
        elif comparison_type == "week":
            period_a_end = now
            period_a_start = now - timedelta(weeks=1)
            period_b_end = now - timedelta(weeks=offset)
            period_b_start = period_b_end - timedelta(weeks=1)
            period_name = f"Last {offset} week(s)"
        elif comparison_type == "month":
            period_a_end = now
            period_a_start = now - timedelta(days=30)
            period_b_end = now - timedelta(days=30 * offset)
            period_b_start = period_b_end - timedelta(days=30)
            period_name = f"Last {offset} month(s)"
        elif comparison_type == "year":
            period_a_end = now
            period_a_start = now - timedelta(days=365)
            period_b_end = now - timedelta(days=365 * offset)
            period_b_start = period_b_end - timedelta(days=365)
            period_name = f"Last {offset} year(s)"
        else:
            raise ValueError(f"Invalid comparison type: {comparison_type}")

        # Calculate metrics for both periods
        period_a_metrics = await self.efficiency_calculator.calculate_area_efficiency(
            area_id, comparison_type, period_a_start, period_a_end
        )

        period_b_metrics = await self.efficiency_calculator.calculate_area_efficiency(
            area_id, comparison_type, period_b_start, period_b_end
        )

        # Calculate deltas
        delta = self._calculate_delta(period_a_metrics, period_b_metrics)

        return {
            "area_id": area_id,
            "comparison_type": comparison_type,
            "period_a": {
                "name": "Current Period",
                "start": period_a_start.isoformat(),
                "end": period_a_end.isoformat(),
                "metrics": period_a_metrics,
            },
            "period_b": {
                "name": period_name,
                "start": period_b_start.isoformat(),
                "end": period_b_end.isoformat(),
                "metrics": period_b_metrics,
            },
            "delta": delta,
            "summary": self._generate_comparison_summary(delta),
        }

    async def compare_custom_periods(
        self,
        area_id: str,
        start_a: datetime,
        end_a: datetime,
        start_b: datetime,
        end_b: datetime,
    ) -> dict[str, Any]:
        """Compare two custom time periods.

        Args:
            area_id: Area ID to compare
            start_a: Start of first period
            end_a: End of first period
            start_b: Start of second period
            end_b: End of second period

        Returns:
            Dictionary containing comparison data
        """
        # Calculate metrics for both periods
        period_a_metrics = await self.efficiency_calculator.calculate_area_efficiency(
            area_id, "custom", start_a, end_a
        )

        period_b_metrics = await self.efficiency_calculator.calculate_area_efficiency(
            area_id, "custom", start_b, end_b
        )

        # Calculate deltas
        delta = self._calculate_delta(period_a_metrics, period_b_metrics)

        return {
            "area_id": area_id,
            "comparison_type": "custom",
            "period_a": {
                "name": "Period A",
                "start": start_a.isoformat(),
                "end": end_a.isoformat(),
                "metrics": period_a_metrics,
            },
            "period_b": {
                "name": "Period B",
                "start": start_b.isoformat(),
                "end": end_b.isoformat(),
                "metrics": period_b_metrics,
            },
            "delta": delta,
            "summary": self._generate_comparison_summary(delta),
        }

    def _calculate_delta(
        self, period_a: dict[str, Any], period_b: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate delta between two periods.

        Args:
            period_a: Metrics for period A (current)
            period_b: Metrics for period B (comparison)

        Returns:
            Delta metrics with percentage changes
        """
        delta = {}

        # Calculate absolute and percentage changes
        metrics = [
            "heating_time_percentage",
            "average_temperature_delta",
            "heating_cycles",
            "energy_score",
            "temperature_stability",
        ]

        for metric in metrics:
            val_a = period_a.get(metric, 0)
            val_b = period_b.get(metric, 0)
            absolute_change = val_a - val_b

            # Calculate percentage change (avoid division by zero)
            if val_b != 0:
                percentage_change = (absolute_change / val_b) * 100
            else:
                percentage_change = 0.0 if val_a == 0 else 100.0

            delta[metric] = {
                "absolute": round(absolute_change, 2),
                "percentage": round(percentage_change, 2),
                "current": round(val_a, 2),
                "previous": round(val_b, 2),
                "improved": self._is_improvement(metric, absolute_change),
            }

        # Estimate energy savings (rough estimate based on efficiency score)
        energy_score_delta = delta["energy_score"]["percentage"]
        delta["estimated_energy_savings"] = {
            "percentage": round(energy_score_delta, 2),
            "description": self._energy_savings_description(energy_score_delta),
        }

        return delta

    def _is_improvement(self, metric: str, change: float) -> bool:
        """Determine if a change is an improvement.

        Args:
            metric: Metric name
            change: Change value (positive or negative)

        Returns:
            True if change represents improvement
        """
        # For these metrics, lower is better
        lower_is_better = [
            "heating_time_percentage",
            "average_temperature_delta",
            "heating_cycles",
            "temperature_stability",
        ]

        # For these metrics, higher is better
        higher_is_better = ["energy_score"]

        if metric in lower_is_better:
            return change < 0
        elif metric in higher_is_better:
            return change > 0
        else:
            return False

    def _generate_comparison_summary(self, delta: dict[str, Any]) -> str:
        """Generate a human-readable summary of the comparison.

        Args:
            delta: Delta metrics

        Returns:
            str: Summary text
        """
        energy_score_change = delta["energy_score"]["percentage"]

        if energy_score_change > 10:
            return (
                f"Efficiency improved by {energy_score_change:.1f}%. "
                f"Great progress in optimizing heating!"
            )
        elif energy_score_change > 0:
            return (
                f"Efficiency slightly improved by {energy_score_change:.1f}%. "
                f"Keep up the good work!"
            )
        elif energy_score_change > -10:
            return (
                f"Efficiency slightly decreased by {abs(energy_score_change):.1f}%. "
                f"This is likely due to weather changes."
            )
        else:
            return (
                f"Efficiency decreased by {abs(energy_score_change):.1f}%. "
                f"Consider checking insulation and heating settings."
            )

    def _energy_savings_description(self, percentage: float) -> str:
        """Generate description of energy savings.

        Args:
            percentage: Percentage change in efficiency score

        Returns:
            Description string
        """
        if percentage > 20:
            return "Significant energy savings achieved!"
        elif percentage > 10:
            return "Moderate energy savings achieved."
        elif percentage > 0:
            return "Slight energy savings achieved."
        elif percentage > -10:
            return "Energy usage slightly increased."
        else:
            return "Energy usage significantly increased."

    async def compare_all_areas(
        self,
        area_manager,
        comparison_type: str,
        offset: int = 1,
    ) -> list[dict[str, Any]]:
        """Compare all areas for a given period.

        Args:
            area_manager: AreaManager instance
            comparison_type: Type of comparison
            offset: Period offset

        Returns:
            List of comparison data for all areas
        """
        results = []

        all_areas = area_manager.get_all_areas()
        for area_id, area in all_areas.items():
            if not area.enabled:
                continue

            try:
                comparison = await self.compare_periods(area_id, comparison_type, offset)
                results.append(comparison)
            except Exception as e:
                _LOGGER.error("Error comparing area %s: %s", area_id, e, exc_info=True)
                continue

        # Sort by energy score improvement (best improvements first)
        results.sort(key=lambda x: x["delta"]["energy_score"]["percentage"], reverse=True)

        return results
