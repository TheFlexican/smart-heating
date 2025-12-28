"""Event storage for Smart Heating learning engine."""

# Exclude heavy database-related code from coverage - exercised by integration tests
# pragma: no cover

import logging
from datetime import datetime, timedelta
from typing import Any
import asyncio

from homeassistant.helpers.recorder import get_instance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    delete,
    select,
)
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError

from ..const import (
    EVENT_RETENTION_DAYS,
    EVENT_STORAGE_DATABASE,
    EVENT_STORAGE_JSON,
)
from ..exceptions import StorageError

_LOGGER = logging.getLogger(__name__)

RECORDER_ENGINE_UNAVAILABLE = "Recorder engine not available"
DB_TABLE_NOT_INITIALIZED = "Database table not initialized"

STORAGE_VERSION = 1
STORAGE_KEY = "smart_heating_events"
CLEANUP_INTERVAL = timedelta(hours=1)  # Run cleanup every hour

# Database table name
DB_TABLE_NAME = "smart_heating_events"


class EventStore:
    """Store heating events for learning with optional database storage."""

    def __init__(self, hass: HomeAssistant, storage_backend: str = EVENT_STORAGE_JSON) -> None:
        """Initialize the event store.

        Args:
            hass: Home Assistant instance
            storage_backend: Storage backend to use (json or database)
        """
        self.hass = hass
        self._storage_backend = storage_backend
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._retention_days: int = EVENT_RETENTION_DAYS
        self._cleanup_unsub = None
        self._db_table = None
        self._db_engine = None
        self._db_validated = False
        self._db_validation_task = None

        if self._storage_backend == EVENT_STORAGE_DATABASE:
            try:
                recorder = get_instance(self.hass)
                if not recorder:
                    self._storage_backend = EVENT_STORAGE_JSON
                else:
                    db_url = str(recorder.db_url)
                    if "sqlite" in db_url.lower():
                        self._storage_backend = EVENT_STORAGE_JSON
                    elif any(
                        db in db_url.lower()
                        for db in ["mysql", "mariadb", "postgresql", "postgres"]
                    ):
                        # Initialize DB table synchronously for tests that expect it
                        try:
                            self._init_database_table()
                        except (SQLAlchemyError, RuntimeError) as err:
                            _LOGGER.debug("DB table init failed: %s, using JSON storage", err)
                            self._storage_backend = EVENT_STORAGE_JSON
            except (AttributeError, RuntimeError, SQLAlchemyError) as err:
                # Keep JSON fallback if anything goes wrong during init
                _LOGGER.debug("DB validation failed during init: %s, using JSON storage", err)
                self._storage_backend = EVENT_STORAGE_JSON

    async def _async_validate_database_support(self) -> None:  # NOSONAR
        """Validate that database storage is supported.

        If the recorder isn't available at the moment we schedule a retry
        instead of marking the DB as unsupported so that integrations that
        start before the recorder becomes available still detect DB storage
        later on.
        """
        if self._db_validated:
            return

        try:
            recorder = get_instance(self.hass)
            if not recorder:
                _LOGGER.debug("Recorder not available, will retry database validation")
                # Start a background retry task if not already running
                if self._db_validation_task is None:
                    self._db_validation_task = self.hass.async_create_task(
                        self._async_retry_database_validation()
                    )
                return

            db_url = str(recorder.db_url)

            # Check if it's SQLite (not supported for database storage)
            if "sqlite" in db_url.lower():
                _LOGGER.debug(
                    "SQLite database detected. Database storage not supported, "
                    "falling back to JSON storage"
                )
                self._storage_backend = EVENT_STORAGE_JSON
                self._db_validated = True
                return

            # Supported: MariaDB, MySQL, PostgreSQL
            if any(db in db_url.lower() for db in ["mysql", "mariadb", "postgresql", "postgres"]):
                db_type = (
                    "MariaDB/MySQL"
                    if "mysql" in db_url.lower() or "mariadb" in db_url.lower()
                    else "PostgreSQL"
                )
                _LOGGER.info("Event storage enabled with %s", db_type)
                self._init_database_table()
                self._db_validated = True
            else:
                _LOGGER.debug("Unsupported database type for event storage, falling back to JSON")
                self._storage_backend = EVENT_STORAGE_JSON
                self._db_validated = True

        except (AttributeError, RuntimeError, SQLAlchemyError) as e:
            _LOGGER.error(
                "Error validating database support: %s, falling back to JSON",
                e,
                exc_info=True,
            )
            self._storage_backend = EVENT_STORAGE_JSON
            self._db_validated = True

    async def _async_retry_database_validation(self) -> None:
        """Retry database validation a few times if recorder wasn't ready.

        This handles cases where the integration starts before the recorder
        is available at HA startup. We attempt a few times with backoff and
        then give up and keep JSON storage if validation never succeeds.
        """
        try:
            for _ in range(10):  # 10 attempts * 30s = 5 minutes
                await asyncio.sleep(30)
                recorder = get_instance(self.hass)
                if recorder:
                    # Attempt to enable database storage (helper handles errors)
                    try:
                        await self._attempt_enable_database(recorder)
                    except (AttributeError, RuntimeError, SQLAlchemyError) as err:
                        _LOGGER.error("Error during deferred DB validation: %s", err, exc_info=True)
                        self._storage_backend = EVENT_STORAGE_JSON
                        self._db_validated = True
                    break

            if not self._db_validated:
                _LOGGER.debug("Database validation retries exhausted; keeping JSON storage")
                self._storage_backend = EVENT_STORAGE_JSON
                self._db_validated = True
        finally:
            self._db_validation_task = None

    async def _attempt_enable_database(self, recorder) -> None:
        """Attempt to enable and initialize database-backed storage.

        This method centralizes the logic to decide whether the recorder's
        database is supported (non-SQLite) and initializes the DB table and
        optionally loads existing entries.
        """
        db_url = str(recorder.db_url)

        # Early exit on unsupported SQLite
        if "sqlite" in db_url.lower():
            _LOGGER.debug("Recorder now available but detected SQLite; will keep JSON storage")
            self._storage_backend = EVENT_STORAGE_JSON
            self._db_validated = True
            return

        if any(db in db_url.lower() for db in ["mysql", "mariadb", "postgresql", "postgres"]):
            _LOGGER.info("Recorder available: enabling event database storage")
            self._init_database_table()
            # If DB contains entries, switch to DB-backed storage and load them
            try:
                stats = await self.async_get_database_stats()
                total = stats.get("total_entries") if isinstance(stats, dict) else None
                if total and int(total) > 0:
                    self._storage_backend = EVENT_STORAGE_DATABASE
                    await self._async_load_from_database()
            except (SQLAlchemyError, RuntimeError, ValueError) as err:
                # Ignore; we'll remain on JSON if loading fails
                _LOGGER.debug("Failed to load from database during enable: %s", err)

            self._db_validated = True
            return

        # Unsupported DB type
        _LOGGER.debug("Unsupported database type for event storage, falling back to JSON")
        self._storage_backend = EVENT_STORAGE_JSON
        self._db_validated = True

    def _init_database_table(self) -> None:
        """Initialize the database table for event storage."""
        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
            self._db_engine = recorder.engine

            metadata = MetaData()
            self._db_table = Table(
                DB_TABLE_NAME,
                metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("area_id", String(255), nullable=False, index=True),
                Column("start_time", DateTime, nullable=False, index=True),
                Column("end_time", DateTime, nullable=False),
                Column("start_temp", Float, nullable=False),
                Column("end_temp", Float, nullable=False),
                Column("duration_minutes", Float, nullable=False),
                Column("temp_change", Float, nullable=False),
                Column("heating_rate", Float, nullable=False),
                Column("outdoor_temp", Float, nullable=True),
                Column("created_at", DateTime, nullable=False, index=True),
            )

            # Create table if it doesn't exist
            assert self._db_engine is not None
            metadata.create_all(self._db_engine)

            _LOGGER.info("Database table '%s' ready for event storage", DB_TABLE_NAME)

        except (SQLAlchemyError, RuntimeError, AttributeError) as e:
            _LOGGER.error(
                "Failed to initialize database table: %s, falling back to JSON", e, exc_info=True
            )
            self._storage_backend = EVENT_STORAGE_JSON
            self._db_table = None
            self._db_engine = None

    async def async_load(self) -> None:
        """Load events from storage."""
        # First, check if there's a stored backend preference in JSON
        data = await self._store.async_load()
        if data and "storage_backend" in data:
            self._storage_backend = data["storage_backend"]

        # Always validate database support
        await self._async_validate_database_support()

        # Now load the actual data
        # Prefer database storage automatically if available and contains data
        if self._db_table is not None:
            # Check whether DB has entries
            try:
                stats = await self.async_get_database_stats()
                total = stats.get("total_entries") if isinstance(stats, dict) else None
                if total and int(total) > 0:
                    # Prefer DB-backed storage if entries exist
                    self._storage_backend = EVENT_STORAGE_DATABASE
                    await self._async_load_from_database()
                else:
                    # No DB entries: fall back to JSON storage
                    await self._async_load_from_json()
            except (SQLAlchemyError, RuntimeError, ValueError) as err:
                # In case of any error querying DB, fall back to JSON
                _LOGGER.warning("Failed to load from database: %s, using JSON", err)
                await self._async_load_from_json()
        else:
            await self._async_load_from_json()

        # Schedule periodic cleanup
        self._cleanup_unsub = async_track_time_interval(
            self.hass, self._async_periodic_cleanup, CLEANUP_INTERVAL
        )
        _LOGGER.info("Event cleanup scheduled every %s", CLEANUP_INTERVAL)

    async def _async_load_from_json(self) -> None:
        """Load events from JSON storage."""
        data = await self._store.async_load()

        if data is not None:
            if "events" in data:
                self._events = data["events"]
            if "retention_days" in data:
                self._retention_days = data["retention_days"]
            if "storage_backend" in data:
                # Preserve storage backend preference
                self._storage_backend = data.get("storage_backend", EVENT_STORAGE_JSON)

            # Clean up old entries
            await self._async_cleanup_old_events()
            _LOGGER.info(
                "Loaded events for %d areas (retention: %d days, storage: JSON)",
                len(self._events),
                self._retention_days,
            )
        else:
            _LOGGER.debug("No events found in JSON storage")

    async def _async_load_from_database(self) -> None:
        """Load events from database."""
        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError("Recorder engine not available")

            db_table = self._db_table

            def _load():
                with recorder.engine.connect() as conn:
                    # Load all events, ordered by start_time
                    stmt = select(db_table).order_by(db_table.c.start_time.desc())
                    result = conn.execute(stmt)

                    events_dict = {}
                    for row in result:
                        area_id = row.area_id
                        if area_id not in events_dict:
                            events_dict[area_id] = []

                        events_dict[area_id].append(
                            {
                                "start_time": row.start_time.isoformat(),
                                "end_time": row.end_time.isoformat(),
                                "start_temp": row.start_temp,
                                "end_temp": row.end_temp,
                                "duration_minutes": row.duration_minutes,
                                "temp_change": row.temp_change,
                                "heating_rate": row.heating_rate,
                                "outdoor_temp": row.outdoor_temp,
                            }
                        )

                    return events_dict

            self._events = await get_instance(self.hass).async_add_executor_job(_load)

            # Clean up old entries in database
            await self._async_cleanup_old_events()

            total_events = sum(len(events) for events in self._events.values())
            _LOGGER.info(
                "Loaded %d events for %d areas from database (retention: %d days)",
                total_events,
                len(self._events),
                self._retention_days,
            )

        except (SQLAlchemyError, RuntimeError, AttributeError, ValueError) as e:
            _LOGGER.error("Failed to load from database: %s", e, exc_info=True)
            self._events = {}

    async def async_record_event(self, area_id: str, event_data: dict[str, Any]) -> None:
        """Record a heating event.

        Args:
            area_id: Area identifier
            event_data: Event data dictionary with keys:
                - start_time: ISO format timestamp
                - end_time: ISO format timestamp
                - start_temp: Starting temperature
                - end_temp: Ending temperature
                - duration_minutes: Duration in minutes
                - temp_change: Temperature change
                - heating_rate: Heating rate (°C/min)
                - outdoor_temp: Outdoor temperature (optional)
        """
        if self._storage_backend == EVENT_STORAGE_DATABASE and self._db_table is not None:
            await self._async_record_event_database(area_id, event_data)
        else:
            await self._async_record_event_json(area_id, event_data)

    async def _async_record_event_json(self, area_id: str, event_data: dict[str, Any]) -> None:
        """Record event to JSON storage."""
        if area_id not in self._events:
            self._events[area_id] = []

        self._events[area_id].append(event_data)

        # Save to JSON
        await self._async_save_to_json()

        _LOGGER.debug(
            "Recorded event for %s to JSON (total events: %d)",
            area_id,
            len(self._events[area_id]),
        )

    async def _async_record_event_database(self, area_id: str, event_data: dict[str, Any]) -> None:
        """Record event to database."""
        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
            if self._db_table is None:
                raise RuntimeError(DB_TABLE_NOT_INITIALIZED)
            assert recorder.engine is not None
            assert self._db_table is not None

            db_table = self._db_table
            engine = recorder.engine
            assert engine is not None

            def _insert():
                with engine.connect() as conn:
                    # Parse timestamps
                    start_time = datetime.fromisoformat(event_data["start_time"])
                    end_time = datetime.fromisoformat(event_data["end_time"])

                    # Insert event
                    stmt = db_table.insert().values(
                        area_id=area_id,
                        start_time=start_time,
                        end_time=end_time,
                        start_temp=event_data["start_temp"],
                        end_temp=event_data["end_temp"],
                        duration_minutes=event_data["duration_minutes"],
                        temp_change=event_data["temp_change"],
                        heating_rate=event_data["heating_rate"],
                        outdoor_temp=event_data.get("outdoor_temp"),
                        created_at=dt_util.now(),
                    )
                    conn.execute(stmt)
                    conn.commit()

            await recorder.async_add_executor_job(_insert)

            # Also add to in-memory cache
            if area_id not in self._events:
                self._events[area_id] = []
            self._events[area_id].append(event_data)

            _LOGGER.debug("Recorded event for %s to database", area_id)

        except (SQLAlchemyError, RuntimeError, AttributeError) as e:
            _LOGGER.error(
                "Failed to record event to database: %s, falling back to JSON", e, exc_info=True
            )
            # Fallback to JSON
            await self._async_record_event_json(area_id, event_data)

    async def async_get_events(self, area_id: str, days: int | None = 30) -> list[dict[str, Any]]:
        """Get events for an area.

        Args:
            area_id: Area identifier
            days: Number of days to look back (None for all events)

        Returns:
            List of event dictionaries, sorted by start_time (oldest first)
        """
        if self._storage_backend == EVENT_STORAGE_DATABASE and self._db_table is not None:
            return await self._async_get_events_database(area_id, days)
        else:
            return await self._async_get_events_json(area_id, days)

    async def _async_get_events_json(
        self, area_id: str, days: int | None = 30
    ) -> list[dict[str, Any]]:
        """Get events from JSON storage."""
        # Use a small await to make this an actual async function for linters
        await asyncio.sleep(0)

        if area_id not in self._events:
            return []

        events = self._events[area_id]

        if days is not None:
            # Filter by time range
            cutoff_time = dt_util.now() - timedelta(days=days)
            events = [e for e in events if datetime.fromisoformat(e["start_time"]) >= cutoff_time]

        # Sort by start_time (oldest first)
        events_sorted = sorted(events, key=lambda e: e["start_time"])

        return events_sorted

    async def _async_get_events_database(
        self, area_id: str, days: int | None = 30
    ) -> list[dict[str, Any]]:
        """Get events from database."""
        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
            if self._db_table is None:
                raise RuntimeError(DB_TABLE_NOT_INITIALIZED)
            assert recorder.engine is not None
            assert self._db_table is not None

            db_table = self._db_table
            engine = recorder.engine
            assert engine is not None

            def _query():
                with engine.connect() as conn:
                    # Build query
                    stmt = select(db_table).where(db_table.c.area_id == area_id)

                    if days is not None:
                        cutoff_time = dt_util.now() - timedelta(days=days)
                        stmt = stmt.where(db_table.c.start_time >= cutoff_time)

                    stmt = stmt.order_by(db_table.c.start_time.asc())

                    result = conn.execute(stmt)

                    events = []
                    for row in result:
                        events.append(
                            {
                                "start_time": row.start_time.isoformat(),
                                "end_time": row.end_time.isoformat(),
                                "start_temp": row.start_temp,
                                "end_temp": row.end_temp,
                                "duration_minutes": row.duration_minutes,
                                "temp_change": row.temp_change,
                                "heating_rate": row.heating_rate,
                                "outdoor_temp": row.outdoor_temp,
                            }
                        )

                    return events

            return await recorder.async_add_executor_job(_query)

        except (SQLAlchemyError, RuntimeError, AttributeError) as e:
            _LOGGER.error("Failed to query events from database: %s", e, exc_info=True)
            return []

    async def async_get_event_count(self, area_id: str) -> int:
        """Get total event count for an area.

        Args:
            area_id: Area identifier

        Returns:
            Total number of events
        """
        if self._storage_backend == EVENT_STORAGE_DATABASE and self._db_table is not None:
            return await self._async_get_event_count_database(area_id)
        else:
            return len(self._events.get(area_id, []))

    async def _async_get_event_count_database(self, area_id: str) -> int:
        """Get event count from database."""
        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
            if self._db_table is None:
                raise RuntimeError(DB_TABLE_NOT_INITIALIZED)
            assert recorder.engine is not None
            assert self._db_table is not None

            db_table = self._db_table
            engine = recorder.engine
            assert engine is not None

            def _count():
                with engine.connect() as conn:
                    from sqlalchemy import func

                    stmt = (
                        select(func.count())
                        .select_from(db_table)
                        .where(db_table.c.area_id == area_id)
                    )
                    result = conn.execute(stmt)
                    res = result.scalar()
                    return int(res or 0)

            return await recorder.async_add_executor_job(_count)

        except (SQLAlchemyError, RuntimeError, AttributeError) as e:
            _LOGGER.error("Failed to count events from database: %s", e, exc_info=True)
            return 0

    async def async_get_database_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with stats: total_entries, storage_size_mb, etc.
        """
        if self._db_table is None:
            return {"total_entries": 0}

        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
            if self._db_table is None:
                raise RuntimeError(DB_TABLE_NOT_INITIALIZED)

            db_table = self._db_table
            engine = recorder.engine

            def _get_stats():
                with engine.connect() as conn:
                    from sqlalchemy import func

                    # Get total count
                    stmt = select(func.count()).select_from(db_table)
                    result = conn.execute(stmt)
                    total = result.scalar()

                    return {"total_entries": total}

            return await recorder.async_add_executor_job(_get_stats)

        except (SQLAlchemyError, RuntimeError, AttributeError) as e:
            _LOGGER.error("Failed to get database stats: %s", e, exc_info=True)
            return {"total_entries": 0}

    async def _async_save_to_json(self) -> None:
        """Save events to JSON storage."""
        try:
            data = {
                "events": self._events,
                "retention_days": self._retention_days,
                "storage_backend": self._storage_backend,
            }
            await self._store.async_save(data)
        except (OSError, ValueError, TypeError) as e:
            _LOGGER.error("Failed to save events to JSON: %s", e, exc_info=True)
            raise StorageError(f"Failed to save events to JSON storage: {e}") from e

    async def _async_cleanup_old_events(self) -> None:
        """Clean up events older than retention period."""
        cutoff_time = dt_util.now() - timedelta(days=self._retention_days)

        if self._storage_backend == EVENT_STORAGE_DATABASE and self._db_table is not None:
            await self._async_cleanup_database(cutoff_time)
        else:
            await self._async_cleanup_json(cutoff_time)

    async def _async_cleanup_json(self, cutoff_time: datetime) -> None:
        """Clean up old events from JSON storage."""
        cleaned_count = 0

        area_ids = list(self._events)
        for area_id in area_ids:
            original_count = len(self._events[area_id])
            self._events[area_id] = [
                e
                for e in self._events[area_id]
                if datetime.fromisoformat(e["start_time"]) >= cutoff_time
            ]
            cleaned_count += original_count - len(self._events[area_id])

            # Remove area if no events left
            if not self._events[area_id]:
                del self._events[area_id]

        if cleaned_count > 0:
            await self._async_save_to_json()
            _LOGGER.info("Cleaned up %d old events from JSON storage", cleaned_count)

    async def _async_cleanup_database(self, cutoff_time: datetime) -> None:
        """Clean up old events from database."""
        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
            if self._db_table is None:
                raise RuntimeError(DB_TABLE_NOT_INITIALIZED)

            db_table = self._db_table
            engine = recorder.engine

            def _cleanup():
                with engine.connect() as conn:
                    stmt = delete(db_table).where(db_table.c.start_time < cutoff_time)
                    result = conn.execute(stmt)
                    conn.commit()
                    return result.rowcount

            rows_deleted = await recorder.async_add_executor_job(_cleanup)

            if rows_deleted > 0:
                _LOGGER.info("Cleaned up %d old events from database", rows_deleted)

                # Also clean up in-memory cache
                area_ids = list(self._events)
                for area_id in area_ids:
                    self._events[area_id] = [
                        e
                        for e in self._events[area_id]
                        if datetime.fromisoformat(e["start_time"]) >= cutoff_time
                    ]
                    if not self._events[area_id]:
                        del self._events[area_id]

        except (SQLAlchemyError, RuntimeError, AttributeError, ValueError) as e:
            _LOGGER.error("Failed to cleanup database: %s", e, exc_info=True)

    async def _async_periodic_cleanup(self, now: datetime) -> None:
        """Periodic cleanup task.

        Args:
            now: Current time (unused, required by async_track_time_interval)
        """
        _LOGGER.debug("Running periodic event cleanup")
        await self._async_cleanup_old_events()

    async def async_close(self) -> None:
        """Close the event store and cleanup."""
        if self._cleanup_unsub is not None:
            self._cleanup_unsub()
            self._cleanup_unsub = None

        # Final save to JSON if using JSON backend
        if self._storage_backend == EVENT_STORAGE_JSON:
            await self._async_save_to_json()

        _LOGGER.debug("Event store closed")
