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
            # Schedule background retry task. Use asyncio.create_task to ensure the
            # coroutine is scheduled under test fixtures that may mock hass.async_create_task.
            asyncio.create_task(self._async_retry_weather_detection())

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
