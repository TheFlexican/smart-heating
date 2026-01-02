"""Tests for Debouncer."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from smart_heating.core.coordination.debouncer import DEFAULT_DEBOUNCE_DELAY, Debouncer


class TestDebouncer:
    """Test Debouncer functionality."""

    def test_init_default(self):
        """Test initialization with default delay."""
        debouncer = Debouncer()
        assert debouncer._delay == DEFAULT_DEBOUNCE_DELAY
        assert debouncer.pending_count == 0

    def test_init_custom_delay(self):
        """Test initialization with custom delay."""
        debouncer = Debouncer(delay=5.0)
        assert debouncer._delay == 5.0

    @pytest.mark.asyncio
    async def test_debounce_executes_callback(self):
        """Test that debounce executes callback after delay."""
        debouncer = Debouncer(delay=0.1)
        callback = AsyncMock()

        await debouncer.async_debounce("test_key", callback)
        await asyncio.sleep(0.15)  # Wait for debounce to complete

        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_debounce_cancels_previous_task(self):
        """Test that debounce cancels previous task for same key."""
        debouncer = Debouncer(delay=0.2)
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        # Start first debounce
        await debouncer.async_debounce("test_key", callback1)
        await asyncio.sleep(0.05)  # Wait a bit

        # Start second debounce with same key (should cancel first)
        await debouncer.async_debounce("test_key", callback2)
        await asyncio.sleep(0.25)  # Wait for second to complete

        # First callback should not have been called (cancelled)
        callback1.assert_not_called()
        # Second callback should have been called
        callback2.assert_called_once()

    @pytest.mark.asyncio
    async def test_debounce_multiple_keys(self):
        """Test that debounce handles multiple keys independently."""
        debouncer = Debouncer(delay=0.1)
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        await debouncer.async_debounce("key1", callback1)
        await debouncer.async_debounce("key2", callback2)
        await asyncio.sleep(0.15)  # Wait for both to complete

        callback1.assert_called_once()
        callback2.assert_called_once()

    @pytest.mark.asyncio
    async def test_has_pending(self):
        """Test has_pending method."""
        debouncer = Debouncer(delay=0.2)
        callback = AsyncMock()

        assert not debouncer.has_pending("test_key")

        await debouncer.async_debounce("test_key", callback)
        assert debouncer.has_pending("test_key")

        await asyncio.sleep(0.25)  # Wait for completion
        assert not debouncer.has_pending("test_key")

    @pytest.mark.asyncio
    async def test_pending_count(self):
        """Test pending_count property."""
        debouncer = Debouncer(delay=0.2)
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        assert debouncer.pending_count == 0

        await debouncer.async_debounce("key1", callback1)
        assert debouncer.pending_count == 1

        await debouncer.async_debounce("key2", callback2)
        assert debouncer.pending_count == 2

        await asyncio.sleep(0.25)  # Wait for completion
        assert debouncer.pending_count == 0

    @pytest.mark.asyncio
    async def test_cancel(self):
        """Test cancel method."""
        debouncer = Debouncer(delay=0.2)
        callback = AsyncMock()

        await debouncer.async_debounce("test_key", callback)
        assert debouncer.has_pending("test_key")

        debouncer.cancel("test_key")
        assert not debouncer.has_pending("test_key")

        await asyncio.sleep(0.25)  # Wait
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_key(self):
        """Test cancel with non-existent key does not raise error."""
        debouncer = Debouncer()
        debouncer.cancel("nonexistent_key")  # Should not raise

    @pytest.mark.asyncio
    async def test_cancel_all(self):
        """Test cancel_all method."""
        debouncer = Debouncer(delay=0.2)
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        await debouncer.async_debounce("key1", callback1)
        await debouncer.async_debounce("key2", callback2)
        assert debouncer.pending_count == 2

        debouncer.cancel_all()
        assert debouncer.pending_count == 0

        await asyncio.sleep(0.25)  # Wait
        callback1.assert_not_called()
        callback2.assert_not_called()

    @pytest.mark.asyncio
    async def test_callback_exception_handling(self):
        """Test that exceptions in callbacks are handled gracefully."""
        debouncer = Debouncer(delay=0.1)

        async def failing_callback():
            raise ValueError("Test error")

        await debouncer.async_debounce("test_key", failing_callback)
        await asyncio.sleep(0.15)  # Wait for callback to fail

        # Should not crash, task should be cleaned up
        assert not debouncer.has_pending("test_key")

    @pytest.mark.asyncio
    async def test_debounce_cleanup_after_completion(self):
        """Test that task is cleaned up after successful completion."""
        debouncer = Debouncer(delay=0.1)
        callback = AsyncMock()

        await debouncer.async_debounce("test_key", callback)
        assert debouncer.has_pending("test_key")

        await asyncio.sleep(0.15)  # Wait for completion

        # Task should be cleaned up
        assert not debouncer.has_pending("test_key")
        callback.assert_called_once()
