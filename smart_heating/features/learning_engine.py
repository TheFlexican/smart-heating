"""Adaptive learning engine for Smart Heating."""

import asyncio
import logging
import statistics
from datetime import datetime
from typing import Any, TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..climate.temperature_sensors import get_outdoor_temperature_from_weather_entity

if TYPE_CHECKING:
    from ..storage.event_store import EventStore

_LOGGER = logging.getLogger(__name__)

# Minimum data points needed before making predictions
MIN_LEARNING_EVENTS = 20
MIN_LEARNING_DAYS = 7


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

    def __init__(self, hass: HomeAssistant, event_store: "EventStore") -> None:
        """Initialize the learning engine.

        Args:
            hass: Home Assistant instance
            event_store: Event store instance for persisting learning data
        """
        self.hass = hass
        self.event_store = event_store
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
            "start_time": dt_util.now(),
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
            end_time=dt_util.now(),
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

        # Record event to event store
        event_data = {
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "start_temp": event.start_temp,
            "end_temp": event.end_temp,
            "duration_minutes": event.duration_minutes,
            "temp_change": event.temp_change,
            "heating_rate": event.heating_rate,
            "outdoor_temp": event.outdoor_temp,
        }

        await self.event_store.async_record_event(area_id, event_data)

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
        """Get recent heating rates from event store.

        Args:
            area_id: Area identifier
            days: Number of days to look back

        Returns:
            List of heating rates
        """
        # Get events from event store
        events = await self.event_store.async_get_events(area_id, days=days)

        # Extract heating rates from events
        rates = [
            event["heating_rate"]
            for event in events
            if event.get("heating_rate") is not None and event["heating_rate"] > 0
        ]

        _LOGGER.debug(
            "Retrieved %d heating rate data points for %s (last %d days)",
            len(rates),
            area_id,
            days,
        )

        return rates

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
        _LOGGER.info("[LEARNING] Querying learning stats for %s", area_id)

        # Get events from event store
        events_30d = await self.event_store.async_get_events(area_id, days=30)
        total_events = await self.event_store.async_get_event_count(area_id)

        # Extract heating rates
        heating_rates = [e["heating_rate"] for e in events_30d if e.get("heating_rate", 0) > 0]

        # Get first and last event times
        first_event_time = None
        last_event_time = None
        if total_events > 0:
            all_events = await self.event_store.async_get_events(area_id, days=None)  # All events
            if all_events:
                first_event_time = all_events[0]["start_time"]
                last_event_time = all_events[-1]["start_time"]

        # Prepare recent events for response (last 10)
        recent_events = []
        for event in events_30d[-10:]:
            recent_events.append(
                {
                    "timestamp": event["start_time"],
                    "heating_rate": round(event["heating_rate"], 4),
                }
            )

        result = {
            "data_points": len(heating_rates),
            "avg_heating_rate": statistics.mean(heating_rates) if heating_rates else 0,
            "min_heating_rate": min(heating_rates) if heating_rates else 0,
            "max_heating_rate": max(heating_rates) if heating_rates else 0,
            "ready_for_predictions": len(heating_rates) >= MIN_LEARNING_EVENTS,
            "outdoor_temp_available": self._weather_entity is not None,
            "first_event_time": first_event_time,
            "last_event_time": last_event_time,
            "recent_events": recent_events,
            "total_events_all_time": total_events,
        }

        _LOGGER.info(
            "[LEARNING] Retrieved learning stats for %s: %d total events, %d data points (last 30 days)",
            area_id,
            result["total_events_all_time"],
            result["data_points"],
        )

        return result
