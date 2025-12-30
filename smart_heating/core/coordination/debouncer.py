"""Debouncer for state change events in Smart Heating integration."""

import asyncio
import logging
from typing import Any, Awaitable, Callable

_LOGGER = logging.getLogger(__name__)

# Default debounce delay in seconds
DEFAULT_DEBOUNCE_DELAY = 2.0


class Debouncer:
    """Debounces state change events to prevent rapid updates.

    Extracts debouncing logic from Coordinator._handle_temperature_change.

    This component:
    - Debounces rapid state changes (e.g., temperature adjustments)
    - Cancels pending tasks when new changes arrive
    - Executes callbacks after the debounce delay
    - Manages task lifecycle and cleanup
    """

    def __init__(self, delay: float = DEFAULT_DEBOUNCE_DELAY) -> None:
        """Initialize debouncer.

        Args:
            delay: Debounce delay in seconds
        """
        self._delay = delay
        self._tasks: dict[str, asyncio.Task] = {}

    async def async_debounce(
        self,
        key: str,
        callback: Callable[[], Awaitable[Any]],
    ) -> None:
        """Debounce a callback for the given key.

        If a debounce task already exists for this key, it will be cancelled
        and a new one will be created.

        Args:
            key: Unique identifier for this debounce operation (e.g., entity_id)
            callback: Async callback to execute after debounce delay
        """
        await asyncio.sleep(0)  # Yield control to event loop
        _LOGGER.debug("Debouncing callback for %s (delay: %.1fs)", key, self._delay)

        # Cancel any existing debounce task for this key
        if key in self._tasks:
            self._tasks[key].cancel()

        # Create new debounced task
        async def debounced_execution() -> None:
            """Execute callback after debounce delay."""
            try:
                await asyncio.sleep(self._delay)
                _LOGGER.debug("Executing debounced callback for %s", key)
                await callback()
            except asyncio.CancelledError:
                _LOGGER.debug("Debounce task cancelled for %s", key)
                raise
            except (ValueError, RuntimeError, AttributeError) as err:
                _LOGGER.error("Error in debounced callback for %s: %s", key, err, exc_info=True)
            finally:
                # Clean up task reference
                if key in self._tasks:
                    del self._tasks[key]

        # Store and start the debounce task
        self._tasks[key] = asyncio.create_task(debounced_execution())

    def cancel(self, key: str) -> None:
        """Cancel pending debounce task for the given key.

        Args:
            key: Key to cancel
        """
        if key in self._tasks:
            _LOGGER.debug("Cancelling debounce task for %s", key)
            self._tasks[key].cancel()
            del self._tasks[key]

    def cancel_all(self) -> None:
        """Cancel all pending debounce tasks."""
        _LOGGER.debug("Cancelling all %d debounce tasks", len(self._tasks))
        for task in self._tasks.values():
            try:
                task.cancel()
            except (asyncio.CancelledError, RuntimeError, AttributeError) as err:
                _LOGGER.debug("Failed to cancel debounce task: %s", err)
        self._tasks.clear()

    def has_pending(self, key: str) -> bool:
        """Check if there is a pending debounce task for the given key.

        Args:
            key: Key to check

        Returns:
            True if there is a pending task, False otherwise
        """
        return key in self._tasks

    @property
    def pending_count(self) -> int:
        """Get the number of pending debounce tasks.

        Returns:
            Number of pending tasks
        """
        return len(self._tasks)
