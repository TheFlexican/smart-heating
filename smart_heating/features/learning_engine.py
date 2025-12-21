"""Adaptive learning engine for Smart Heating."""

import asyncio
import logging
import statistics
from datetime import datetime
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    StatisticData,
    StatisticMetaData,
    async_add_external_statistics,
    statistics_during_period,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from ..climate.temperature_sensors import get_outdoor_temperature_from_weather_entity

_LOGGER = logging.getLogger(__name__)

# Minimum data points needed before making predictions
MIN_LEARNING_EVENTS = 20
MIN_LEARNING_DAYS = 7

# Statistic IDs for different metrics
STAT_HEATING_RATE = "smart_heating:heating_rate_{area_id}"
STAT_COOLDOWN_RATE = "smart_heating:cooldown_rate_{area_id}"
STAT_OUTDOOR_CORRELATION = "smart_heating:outdoor_correlation_{area_id}"
STAT_PREDICTION_ACCURACY = "smart_heating:prediction_accuracy_{area_id}"


class HeatingEvent:
    """Represents a single heating event for learning."""

    def __init__(
        self,
        area_id: str,
        start_time: datetime,
        end_time: datetime,
        start_temp: float,
        end_temp: float,
        outdoor_temp: float | None = None,
    ):
        """Initialize heating event.

        Args:
            area_id: Area identifier
            start_time: When heating started
            end_time: When heating ended
            start_temp: Temperature at start
            end_temp: Temperature at end
            outdoor_temp: Outdoor temperature during event
        """
        self.area_id = area_id
        self.start_time = start_time
        self.end_time = end_time
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.outdoor_temp = outdoor_temp

        # Calculate derived metrics
        self.duration_minutes = (end_time - start_time).total_seconds() / 60
        self.temp_change = end_temp - start_temp
        self.heating_rate = (
            self.temp_change / self.duration_minutes if self.duration_minutes > 0 else 0
        )


class LearningEngine:
    """Engine for learning heating patterns and making predictions."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the learning engine.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._active_heating_events: dict[str, dict[str, Any]] = {}
        self._weather_entity: str | None = None

        _LOGGER.debug("Learning engine initialized")

    async def async_setup(self) -> None:
        """Set up the learning engine."""
        # Auto-detect weather entity
        self._weather_entity = await self._async_detect_weather_entity()

        # If detection failed, schedule retries
        if not self._weather_entity:
            _LOGGER.warning("No weather entity detected at startup - will retry for 5 minutes")
            self.hass.async_create_task(self._async_retry_weather_detection())

        # Register statistics metadata for all metrics
        await self._async_register_statistics_metadata()

        _LOGGER.info("Learning engine setup complete (weather entity: %s)", self._weather_entity)

    async def _async_detect_weather_entity(
        self,
    ) -> str | None:  # NOSONAR - intentionally async (PB: no await inside; awaited externally)
        """Auto-detect the weather entity.

        Returns:
            Weather entity ID or None if not found
        """
        # Look for weather entities
        for entity_id in self.hass.states.async_entity_ids("weather"):
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unknown", "unavailable"):
                _LOGGER.info("Auto-detected weather entity: %s", entity_id)
                return entity_id

        _LOGGER.debug("No weather entity found - outdoor temperature correlation disabled")
        return None

    async def _async_retry_weather_detection(self) -> None:
        """Retry weather entity detection with backoff.

        Retries every 30 seconds for up to 5 minutes to handle cases where
        weather integration loads after smart_heating at HA startup.
        """
        _LOGGER.info("Weather entity retry task started - will check every 30 seconds")

        for attempt in range(10):  # 10 attempts * 30s = 5 minutes
            await asyncio.sleep(30)
            _LOGGER.info("Weather entity retry attempt %d/10", attempt + 1)

            self._weather_entity = await self._async_detect_weather_entity()
            if self._weather_entity:
                state = self.hass.states.get(self._weather_entity)
                temp = state.attributes.get("temperature") if state else None
                _LOGGER.info(
                    "Weather entity detected on retry %d/10: %s (current temp: %s°C)",
                    attempt + 1,
                    self._weather_entity,
                    temp,
                )
                return

        _LOGGER.warning(
            "Failed to detect weather entity after 10 retries - "
            "outdoor temperature correlation will remain disabled"
        )

    async def _async_register_statistics_metadata(
        self,
    ) -> None:  # NOSONAR - intentionally async (registration may occur asynchronously)
        """Register metadata for statistics tracking."""
        # We'll register metadata when we first record data for each area
        # This is done dynamically per area
        pass

    def _get_statistic_id(self, metric_type: str, area_id: str) -> str:
        """Get statistic ID for a metric type and area.

        Args:
            metric_type: Type of metric (heating_rate, cooldown_rate, etc.)
            area_id: Area identifier

        Returns:
            Statistic ID string
        """
        return f"smart_heating:{metric_type}_{area_id}"

    async def _async_ensure_statistic_metadata(
        self, area_id: str, metric_type: str, name: str, unit: str
    ) -> None:  # NOSONAR - intentionally async (registration API is asynchronous in HA)
        """Ensure statistic metadata is registered.

        Args:
            area_id: Area identifier
            metric_type: Type of metric
            name: Display name
            unit: Unit of measurement
        """
        statistic_id = self._get_statistic_id(metric_type, area_id)

        metadata = StatisticMetaData(
            has_mean=True,
            has_sum=False,
            name=name,
            source="smart_heating",
            statistic_id=statistic_id,
            unit_of_measurement=unit,
            mean_type="mean",  # Required for HA 2025.11+ compatibility
        )

        async_add_external_statistics(self.hass, metadata, [])

    async def async_start_heating_event(
        self,
        area_id: str,
        current_temp: float,
    ) -> None:
        """Record the start of a heating event.

        Args:
            area_id: Area identifier
            current_temp: Current temperature when heating started
        """
        outdoor_temp = await self._async_get_outdoor_temperature()

        self._active_heating_events[area_id] = {
            "start_time": datetime.now(),
            "start_temp": current_temp,
            "outdoor_temp": outdoor_temp,
        }

        _LOGGER.info(
            "[LEARNING] Started heating event for %s: temp=%.1f°C, outdoor=%.1f°C",
            area_id,
            current_temp,
            outdoor_temp or 0,
        )

    async def async_end_heating_event(
        self,
        area_id: str,
        current_temp: float,
    ) -> None:
        """Record the end of a heating event and calculate learning metrics.

        Args:
            area_id: Area identifier
            current_temp: Current temperature when heating ended
            target_reached: Whether target temperature was reached
        """
        _LOGGER.info(
            "[LEARNING] Ending heating event for %s (current temp: %.1f°C)",
            area_id,
            current_temp,
        )

        if area_id not in self._active_heating_events:
            _LOGGER.warning(
                "[LEARNING] No active heating event for %s to end - event was never started or already ended",
                area_id,
            )
            return

        event_data = self._active_heating_events.pop(area_id)

        event = HeatingEvent(
            area_id=area_id,
            start_time=event_data["start_time"],
            end_time=datetime.now(),
            start_temp=event_data["start_temp"],
            end_temp=current_temp,
            outdoor_temp=event_data.get("outdoor_temp"),
        )

        # Only record meaningful events (>5 minutes, >0.1°C change)
        if event.duration_minutes < 5 or abs(event.temp_change) < 0.1:
            _LOGGER.warning(
                "[LEARNING] Skipping short/insignificant heating event for %s "
                "(duration: %.1f min < 5 min, temp change: %.2f°C < 0.1°C) - "
                "Event not stored in database",
                area_id,
                event.duration_minutes,
                event.temp_change,
            )
            return

        # Record to statistics
        await self._async_record_heating_event(event)

        _LOGGER.info(
            "[LEARNING] ✓ Heating event recorded for %s: %.1f°C → %.1f°C in %.1f min "
            "(rate: %.3f°C/min, outdoor: %.1f°C)",
            area_id,
            event.start_temp,
            event.end_temp,
            event.duration_minutes,
            event.heating_rate,
            event.outdoor_temp or 0,
        )

    async def _async_record_heating_event(self, event: HeatingEvent) -> None:
        """Record heating event to statistics database.

        Args:
            event: HeatingEvent instance
        """
        statistic_id = self._get_statistic_id("heating_rate", event.area_id)
        _LOGGER.info(
            "[LEARNING] Recording heating event to database for %s (statistic_id: %s)",
            event.area_id,
            statistic_id,
        )

        try:
            # Ensure metadata is registered
            await self._async_ensure_statistic_metadata(
                event.area_id,
                "heating_rate",
                f"Heating Rate - {event.area_id}",
                "°C/min",
            )

            # Record heating rate
            statistics_data = [
                StatisticData(
                    start=event.start_time,
                    mean=event.heating_rate,
                    state=event.heating_rate,
                )
            ]

            metadata = StatisticMetaData(
                has_mean=True,
                has_sum=False,
                name=f"Heating Rate - {event.area_id}",
                source="smart_heating",
                statistic_id=statistic_id,
                unit_of_measurement="°C/min",
                mean_type="mean",  # Required for HA 2025.11+ compatibility
                unit_class="temperature",  # Required to prevent runtime errors
            )

            # Add statistics asynchronously
            await get_instance(self.hass).async_add_executor_job(
                async_add_external_statistics, self.hass, metadata, statistics_data
            )

            _LOGGER.info(
                "[LEARNING] ✓ Successfully recorded heating rate statistic for %s: %.3f°C/min (statistic_id: %s)",
                event.area_id,
                event.heating_rate,
                statistic_id,
            )

            # Record outdoor correlation if available
            if event.outdoor_temp is not None:
                await self._async_record_outdoor_correlation(event)
        except Exception as err:
            _LOGGER.error(
                "[LEARNING] ✗ Failed to record heating event for %s (statistic_id: %s): %s",
                event.area_id,
                statistic_id,
                err,
                exc_info=True,
            )

    async def _async_record_outdoor_correlation(self, event: HeatingEvent) -> None:
        """Record outdoor temperature correlation.

        Args:
            event: HeatingEvent instance
        """
        try:
            await self._async_ensure_statistic_metadata(
                event.area_id,
                "outdoor_correlation",
                f"Outdoor Temp - {event.area_id}",
                UnitOfTemperature.CELSIUS,
            )

            statistic_id = self._get_statistic_id("outdoor_correlation", event.area_id)
            statistics_data = [
                StatisticData(
                    start=event.start_time,
                    mean=event.outdoor_temp,
                    state=event.outdoor_temp,
                )
            ]

            metadata = StatisticMetaData(
                has_mean=True,
                has_sum=False,
                name=f"Outdoor Temp During Heating - {event.area_id}",
                source="smart_heating",
                statistic_id=statistic_id,
                unit_of_measurement=UnitOfTemperature.CELSIUS,
                mean_type="mean",  # Required for HA 2025.11+ compatibility
                unit_class="temperature",  # Required to prevent runtime errors
            )

            await get_instance(self.hass).async_add_executor_job(
                async_add_external_statistics, self.hass, metadata, statistics_data
            )

            _LOGGER.debug(
                "Recorded outdoor correlation for %s: %.1f°C",
                event.area_id,
                event.outdoor_temp,
            )
        except Exception as err:
            _LOGGER.error("Failed to record outdoor correlation for %s: %s", event.area_id, err)

    async def _async_get_outdoor_temperature(
        self,
    ) -> float | None:  # NOSONAR - intentionally async (awaited by callers)
        """Get current outdoor temperature from weather entity.

        Delegates to centralized helper for consistent weather entity access.

        Returns:
            Outdoor temperature in Celsius or None if unavailable
        """
        return get_outdoor_temperature_from_weather_entity(self.hass, self._weather_entity)

    async def async_predict_heating_time(
        self,
        area_id: str,
        current_temp: float,
        target_temp: float,
    ) -> int | None:
        """Predict how many minutes needed to heat from current to target.

        Args:
            area_id: Area identifier
            current_temp: Current temperature
            target_temp: Target temperature

        Returns:
            Predicted minutes or None if insufficient data
        """
        # Get recent heating rate statistics
        heating_rates = await self._async_get_recent_heating_rates(area_id, days=30)

        if len(heating_rates) < MIN_LEARNING_EVENTS:
            _LOGGER.debug(
                "Insufficient data for prediction (need %d events, have %d)",
                MIN_LEARNING_EVENTS,
                len(heating_rates),
            )
            return None

        # Calculate average heating rate
        avg_rate = statistics.mean(heating_rates)

        # Adjust for outdoor temperature if available
        outdoor_temp = await self._async_get_outdoor_temperature()
        if outdoor_temp is not None:
            adjustment = await self._async_calculate_outdoor_adjustment(outdoor_temp)
            avg_rate *= adjustment

        # Calculate predicted time
        temp_change = target_temp - current_temp
        if temp_change <= 0 or avg_rate <= 0:
            return 0

        predicted_minutes = temp_change / avg_rate

        _LOGGER.debug(
            "Predicted heating time for %s: %.1f min (%.1f°C → %.1f°C at %.3f°C/min)",
            area_id,
            predicted_minutes,
            current_temp,
            target_temp,
            avg_rate,
        )

        return int(predicted_minutes)

    async def _async_get_recent_heating_rates(self, area_id: str, days: int = 30) -> list[float]:
        """Get recent heating rates from statistics.

        Args:
            area_id: Area identifier
            days: Number of days to look back

        Returns:
            List of heating rates
        """
        from datetime import timedelta

        statistic_id = self._get_statistic_id("heating_rate", area_id)

        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        try:
            # Get statistics from recorder using statistics_during_period
            stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period,
                self.hass,
                start_time,
                end_time,
                {statistic_id},
                "hour",  # period
                None,  # units
                {"mean"},  # types
            )

            if not stats or statistic_id not in stats:
                _LOGGER.debug("No heating rate statistics found for %s", area_id)
                return []

            # Extract mean values
            rates = [
                s["mean"]
                for s in stats[statistic_id]
                if s.get("mean") is not None and s["mean"] > 0
            ]

            _LOGGER.debug(
                "Retrieved %d heating rate data points for %s (last %d days)",
                len(rates),
                area_id,
                days,
            )

            return rates
        except Exception as err:
            _LOGGER.error("Failed to retrieve heating rates for %s: %s", area_id, err)
            return []

    async def _async_calculate_outdoor_adjustment(self, current_outdoor_temp: float) -> float:
        """Calculate heating rate adjustment based on outdoor temperature.

        Args:
            current_outdoor_temp: Current outdoor temperature

        Returns:
            Adjustment factor (1.0 = no change, >1 = faster, <1 = slower)
        """
        await asyncio.sleep(0)  # Minimal async operation to satisfy async requirement
        # For now, simple linear adjustment
        # Colder outdoor = slower heating
        # This will be improved with actual correlation data later

        if current_outdoor_temp >= 15:
            return 1.1  # Slightly faster when warm outside
        elif current_outdoor_temp >= 5:
            return 1.0  # Normal
        elif current_outdoor_temp >= 0:
            return 0.9  # Slightly slower when cold
        else:
            return 0.8  # Slower when very cold

    async def async_calculate_smart_boost_offset(
        self,
        area_id: str,
    ) -> float | None:  # NOSONAR - intentionally async (implementation improved)
        """Calculate optimal boost offset based on learning data.

        The algorithm uses recent heating rate statistics to estimate how much
        temperature is lost during inactive periods and recommends a small offset (in °C) to
        compensate. The estimate is conservative and will return ``None`` when
        there is insufficient data.

        Args:
            area_id: Area identifier

        Returns:
            Recommended boost offset (rounded to 1 decimal) or ``None`` if
            insufficient data or negligible boost suggested
        """
        # Gather recent heating rate statistics (°C per minute)
        heating_rates = await self._async_get_recent_heating_rates(area_id, days=30)

        if len(heating_rates) < MIN_LEARNING_EVENTS:
            _LOGGER.debug(
                "Insufficient data for smart boost (need %d events, have %d)",
                MIN_LEARNING_EVENTS,
                len(heating_rates),
            )
            return None

        # Average heating rate (°C/min)
        avg_rate = statistics.mean(heating_rates)

        # Estimate overnight cooling: assume an 8-hour night and convert to minutes
        # so that °C/min × minutes = °C. Cooling is a small fraction of the heating
        # rate since heating is an active process while cooling is passive.
        hours_night = 8
        minutes_night = hours_night * 60
        # Cooling fraction is intentionally small (5% here) and can be tuned later
        cooling_fraction = 0.05
        estimated_overnight_cooling = avg_rate * minutes_night * cooling_fraction

        # Adjust estimate by outdoor temperature if available (colder outside -> more cooling)
        outdoor_temp = await self._async_get_outdoor_temperature()
        adjustment = 1.0
        if outdoor_temp is not None:
            # 2% extra cooling per °C below 10°C, capped to reasonable bounds
            adjustment += max(0.0, (10.0 - outdoor_temp) * 0.02)
            adjustment = min(adjustment, 1.5)  # cap

        # Apply adjustment and cap to avoid unrealistic offsets
        max_boost = 3.0  # °C - safety cap
        boost = estimated_overnight_cooling * adjustment
        boost = min(boost, max_boost)

        # If the suggested boost is negligible, don't recommend anything
        if boost < 0.1:
            _LOGGER.debug("Calculated boost offset negligible (%.3f°C) for %s", boost, area_id)
            return None

        # Round to one decimal for user-friendly offsets
        result = round(boost, 1)
        _LOGGER.debug(
            "Calculated boost offset for %s: %.1f°C (avg_rate=%.3f°C/min, outdoor=%s)",
            area_id,
            result,
            avg_rate,
            str(outdoor_temp),
        )
        return result

    async def async_get_learning_stats(self, area_id: str) -> dict[str, Any]:
        """Get learning statistics for an area.

        Args:
            area_id: Area identifier

        Returns:
            Dictionary with learning statistics
        """
        from datetime import timedelta

        statistic_id = self._get_statistic_id("heating_rate", area_id)
        _LOGGER.info(
            "[LEARNING] Querying learning stats for %s (statistic_id: %s)",
            area_id,
            statistic_id,
        )

        # Get detailed statistics from database
        detailed_stats = await self._async_get_detailed_statistics(area_id, days=30)

        # Get basic heating rates for compatibility
        heating_rates = detailed_stats.get("heating_rates", [])

        result = {
            "data_points": len(heating_rates),
            "avg_heating_rate": statistics.mean(heating_rates) if heating_rates else 0,
            "min_heating_rate": min(heating_rates) if heating_rates else 0,
            "max_heating_rate": max(heating_rates) if heating_rates else 0,
            "ready_for_predictions": len(heating_rates) >= MIN_LEARNING_EVENTS,
            "outdoor_temp_available": self._weather_entity is not None,
            "first_event_time": detailed_stats.get("first_event_time"),
            "last_event_time": detailed_stats.get("last_event_time"),
            "recent_events": detailed_stats.get("recent_events", []),
            "total_events_all_time": detailed_stats.get("total_events_all_time", 0),
        }

        _LOGGER.info(
            "[LEARNING] Retrieved learning stats for %s: %d total events, %d data points (last 30 days)",
            area_id,
            result["total_events_all_time"],
            result["data_points"],
        )

        return result

    async def _async_get_detailed_statistics(self, area_id: str, days: int = 30) -> dict[str, Any]:
        """Get detailed learning statistics from database.

        Args:
            area_id: Area identifier
            days: Number of days to look back

        Returns:
            Dictionary with detailed statistics
        """
        from datetime import timedelta
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.statistics import (
            statistics_during_period,
        )

        statistic_id = self._get_statistic_id("heating_rate", area_id)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        _LOGGER.info(
            "[LEARNING] Querying database for %s (statistic_id: %s, period: %s to %s)",
            area_id,
            statistic_id,
            start_time.isoformat(),
            end_time.isoformat(),
        )

        try:
            # Get statistics for the period
            stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period,
                self.hass,
                start_time,
                end_time,
                {statistic_id},
                "hour",
                None,
                {"mean"},
            )

            # Get all-time statistics for total count
            # Use a very old date instead of None (HA 2025+ doesn't accept None)
            all_time_start = datetime(1970, 1, 1)
            all_time_stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period,
                self.hass,
                all_time_start,  # Start from Unix epoch to get all-time stats
                end_time,
                {statistic_id},
                "hour",
                None,
                {"mean"},
            )

            if not stats or statistic_id not in stats:
                _LOGGER.warning(
                    "[LEARNING] No heating rate statistics found in database for %s (statistic_id: %s) - "
                    "Either no events have been recorded yet, or there's a mismatch in area_id format",
                    area_id,
                    statistic_id,
                )
                return {
                    "heating_rates": [],
                    "recent_events": [],
                    "total_events_all_time": 0,
                }

            stat_data = stats[statistic_id]
            all_time_data = all_time_stats.get(statistic_id, []) if all_time_stats else []

            # Extract heating rates
            heating_rates = [
                s["mean"] for s in stat_data if s.get("mean") is not None and s["mean"] > 0
            ]

            # Get recent events (last 10)
            recent_events = []
            for stat in reversed(stat_data[-10:]):
                if stat.get("mean") is not None and stat["mean"] > 0:
                    recent_events.append(
                        {
                            "timestamp": stat.get("start", stat.get("end")).isoformat(),
                            "heating_rate": round(stat["mean"], 4),
                        }
                    )

            # Get first and last event times
            first_event_time = None
            last_event_time = None

            if all_time_data:
                first_valid = next(
                    (s for s in all_time_data if s.get("mean") is not None and s["mean"] > 0), None
                )
                if first_valid:
                    first_event_time = first_valid.get("start", first_valid.get("end"))
                    if first_event_time:
                        first_event_time = first_event_time.isoformat()

            if stat_data:
                last_valid = next(
                    (s for s in reversed(stat_data) if s.get("mean") is not None and s["mean"] > 0),
                    None,
                )
                if last_valid:
                    last_event_time = last_valid.get("start", last_valid.get("end"))
                    if last_event_time:
                        last_event_time = last_event_time.isoformat()

            return {
                "heating_rates": heating_rates,
                "recent_events": recent_events,
                "first_event_time": first_event_time,
                "last_event_time": last_event_time,
                "total_events_all_time": len(
                    [s for s in all_time_data if s.get("mean") is not None and s["mean"] > 0]
                ),
            }

        except Exception as err:
            _LOGGER.error("Error getting detailed statistics for %s: %s", area_id, err)
            return {
                "heating_rates": [],
                "recent_events": [],
                "total_events_all_time": 0,
            }
