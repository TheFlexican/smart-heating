"""Device management and event logging service."""

import asyncio
import inspect
import logging
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ...exceptions import DeviceError, ValidationError
from ...const import TIMEZONE_SUFFIX
from ...models import DeviceEvent

_LOGGER = logging.getLogger(__name__)

# Use centralized timezone suffix constant
UTC_SUFFIX = TIMEZONE_SUFFIX


class DeviceService:
    """Handles device management and event logging."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize device service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

        # Device event logging (in-memory per-area circular buffer)
        self._device_log_capacity: int = 500
        self._device_logs: dict[str, Deque[DeviceEvent]] = {}
        self._device_event_retention_minutes: int = 60  # minutes
        self._device_log_listeners: list = []

    def add_device_to_area(
        self,
        area: Any,  # Area type to avoid circular import
        device_id: str,
        device_type: str,
        mqtt_topic: str | None = None,
    ) -> None:
        """Add a device to an area.

        Args:
            area: Area instance
            device_id: Device identifier
            device_type: Type of device
            mqtt_topic: MQTT topic for the device
        """
        area.add_device(device_id, device_type, mqtt_topic)
        _LOGGER.debug("Added device %s to area %s", device_id, area.area_id)

    def remove_device_from_area(
        self,
        area: Any,  # Area type to avoid circular import
        device_id: str,
    ) -> None:
        """Remove a device from an area.

        Args:
            area: Area instance
            device_id: Device identifier
        """
        area.remove_device(device_id)
        _LOGGER.debug("Removed device %s from area %s", device_id, area.area_id)

    def async_add_device_event(self, area_id: str, event: DeviceEvent) -> None:
        """Add a device event to the per-area logs and notify listeners.

        Note: Named "async_" to indicate it may schedule coroutines; it is a
        synchronous helper so tests can call it without awaiting.

        Args:
            area_id: Area identifier
            event: Device event to log
        """
        if area_id not in self._device_logs:
            self._device_logs[area_id] = deque(maxlen=self._device_log_capacity)

        self._device_logs[area_id].appendleft(event)
        self._purge_old_events(area_id)
        self._notify_device_log_listeners(event)

    def _purge_old_events(self, area_id: str) -> None:
        """Remove events older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=self._device_event_retention_minutes
        )
        while self._device_logs[area_id]:
            if not self._is_event_expired(self._device_logs[area_id][-1], cutoff):
                break
            self._device_logs[area_id].pop()

    def _is_event_expired(self, event: DeviceEvent, cutoff: datetime) -> bool:
        """Check if an event is older than the cutoff time."""
        try:
            ts = event.timestamp
            ts_dt = datetime.fromisoformat(ts.replace("Z", UTC_SUFFIX))
            return ts_dt < cutoff
        except (HomeAssistantError, DeviceError, ValidationError, AttributeError, ValueError):
            # If parsing fails, keep the event
            return False

    def _notify_device_log_listeners(self, event: DeviceEvent) -> None:
        """Notify all registered listeners of a new device event."""
        event_dict = event.to_dict() if hasattr(event, "to_dict") else event
        for listener in self._device_log_listeners:
            self._call_listener(listener, event_dict)

    def _call_listener(self, listener, event_dict: dict) -> None:
        """Call a single listener, handling async and sync cases."""
        try:
            # Use inspect.iscoroutinefunction instead of asyncio.iscoroutinefunction
            # (deprecated) to detect coroutine functions reliably.
            if inspect.iscoroutinefunction(listener):
                self._schedule_async_listener(listener, event_dict)
            else:
                listener(event_dict)
        except (HomeAssistantError, DeviceError, ValidationError, AttributeError):
            _LOGGER.exception("Device log listener failed")

    def _schedule_async_listener(self, listener, event_dict: dict) -> None:
        """Schedule an async listener to run."""
        try:
            task = self.hass.async_create_task(listener(event_dict))
        except (HomeAssistantError, DeviceError, ValidationError, AttributeError):
            task = asyncio.create_task(listener(event_dict))
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    def async_get_device_logs(
        self,
        area_id: str,
        device_id: str | None = None,
        direction: str | None = None,
        since: str | None = None,
    ) -> list[dict]:
        """Retrieve device logs with optional filtering.

        Args:
            area_id: Area identifier
            device_id: Optional device ID filter
            direction: Optional direction filter (inbound/outbound)
            since: Optional ISO timestamp to filter events after

        Returns:
            List of device event dicts, newest-first
        """
        if area_id not in self._device_logs:
            return []

        # The deque is iterable; avoid an unnecessary copy by iterating it
        # directly. Filtering below produces new lists as needed.
        events = self._device_logs[area_id]

        # Filter by device_id and direction
        if device_id is not None:
            events = [e for e in events if getattr(e, "device_id", None) == device_id]
        if direction is not None:
            events = [e for e in events if getattr(e, "direction", None) == direction]

        # Filter by since (ISO timestamp string)
        if since is not None:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", UTC_SUFFIX))
            except (HomeAssistantError, DeviceError, ValidationError, AttributeError, ValueError):
                since_dt = None

            def since_filter(e):
                try:
                    ts = datetime.fromisoformat(e.timestamp.replace("Z", UTC_SUFFIX))
                    return ts >= since_dt if since_dt is not None else True
                except (
                    HomeAssistantError,
                    DeviceError,
                    ValidationError,
                    AttributeError,
                    ValueError,
                ):
                    # If parsing fails for the event, include it
                    return True

            events = [e for e in events if since_filter(e)]

        # Convert to dicts and return
        return [e.to_dict() if hasattr(e, "to_dict") else e for e in events]

    def add_device_log_listener(self, cb) -> None:
        """Register a callback to receive device events.

        Args:
            cb: Callback function to register (can be async or sync)
        """
        if cb not in self._device_log_listeners:
            self._device_log_listeners.append(cb)
            _LOGGER.debug("Added device log listener")

    def remove_device_log_listener(self, cb) -> None:
        """Remove a previously registered listener.

        Args:
            cb: Callback function to remove
        """
        try:
            self._device_log_listeners.remove(cb)
            _LOGGER.debug("Removed device log listener")
        except ValueError:
            pass
