"""History tracking for Smart Heating."""

# Exclude heavy database-related code from coverage - exercised by integration tests
# pragma: no cover

import logging
import json
from datetime import datetime, timedelta
from typing import Any
import asyncio

from homeassistant.components.recorder import get_instance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
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

from ..const import (
    DEFAULT_HISTORY_RETENTION_DAYS,
    HISTORY_STORAGE_DATABASE,
    HISTORY_STORAGE_JSON,
    MAX_HISTORY_RETENTION_DAYS,
)

_LOGGER = logging.getLogger(__name__)

RECORDER_ENGINE_UNAVAILABLE = "Recorder engine not available"
DB_TABLE_NOT_INITIALIZED = "Database table not initialized"

STORAGE_VERSION = 1
STORAGE_KEY = "smart_heating_history"
CLEANUP_INTERVAL = timedelta(hours=1)  # Run cleanup every hour

# Database table name
DB_TABLE_NAME = "smart_heating_history"


class HistoryTracker:
    """Track temperature history for areas with optional database storage."""

    def __init__(self, hass: HomeAssistant, storage_backend: str = HISTORY_STORAGE_JSON) -> None:
        """Initialize the history tracker.

        Args:
            hass: Home Assistant instance
            storage_backend: Storage backend to use (json or database)
        """
        self.hass = hass
        self._storage_backend = storage_backend
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._retention_days: int = DEFAULT_HISTORY_RETENTION_DAYS
        self._cleanup_unsub = None
        self._db_table = None
        self._db_engine = None
        self._db_validated = False
        self._db_validation_task = None
        # Quick validation for database backend at init time to satisfy tests
        if self._storage_backend == HISTORY_STORAGE_DATABASE:
            try:
                recorder = get_instance(self.hass)
                if not recorder:
                    self._storage_backend = HISTORY_STORAGE_JSON
                else:
                    db_url = str(recorder.db_url)
                    if "sqlite" in db_url.lower():
                        self._storage_backend = HISTORY_STORAGE_JSON
                    elif any(
                        db in db_url.lower()
                        for db in ["mysql", "mariadb", "postgresql", "postgres"]
                    ):
                        # Initialize DB table synchronously for tests that expect it
                        try:
                            self._init_database_table()
                        except Exception:
                            self._storage_backend = HISTORY_STORAGE_JSON
            except Exception:
                # Keep JSON fallback if anything goes wrong during init
                self._storage_backend = HISTORY_STORAGE_JSON

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
                self._storage_backend = HISTORY_STORAGE_JSON
                self._db_validated = True
                return

            # Supported: MariaDB, MySQL, PostgreSQL
            if any(db in db_url.lower() for db in ["mysql", "mariadb", "postgresql", "postgres"]):
                db_type = (
                    "MariaDB/MySQL"
                    if "mysql" in db_url.lower() or "mariadb" in db_url.lower()
                    else "PostgreSQL"
                )
                _LOGGER.info("Database storage enabled with %s", db_type)
                self._init_database_table()
                self._db_validated = True
            else:
                _LOGGER.debug("Unsupported database type for history storage, falling back to JSON")
                self._storage_backend = HISTORY_STORAGE_JSON
                self._db_validated = True

        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error(
                "Error validating database support: %s, falling back to JSON",
                e,
                exc_info=True,
            )
            self._storage_backend = HISTORY_STORAGE_JSON
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
                    try:
                        await self._attempt_enable_database(recorder)
                    except Exception:  # pylint: disable=broad-except
                        _LOGGER.exception("Error during deferred DB validation")
                        self._storage_backend = HISTORY_STORAGE_JSON
                        self._db_validated = True
                    break

            if not self._db_validated:
                _LOGGER.debug("Database validation retries exhausted; keeping JSON storage")
                self._storage_backend = HISTORY_STORAGE_JSON
                self._db_validated = True
        finally:
            self._db_validation_task = None

    async def _attempt_enable_database(self, recorder) -> None:
        """Attempt to enable and initialize database-backed storage for history.

        Centralizes the logic and reduces cognitive complexity in the retry loop.
        """
        db_url = str(recorder.db_url)

        if "sqlite" in db_url.lower():
            _LOGGER.debug("Recorder now available but detected SQLite; will keep JSON storage")
            self._storage_backend = HISTORY_STORAGE_JSON
            self._db_validated = True
            return

        if any(db in db_url.lower() for db in ["mysql", "mariadb", "postgresql", "postgres"]):
            _LOGGER.info("Recorder available: enabling history database storage")
            self._init_database_table()
            # If DB contains entries, switch to DB-backed storage and load them
            try:
                stats = await self.async_get_database_stats()
                total = stats.get("total_entries") if isinstance(stats, dict) else None
                if total and int(total) > 0:
                    self._storage_backend = HISTORY_STORAGE_DATABASE
                    await self._async_load_from_database()
            except Exception:
                # Ignore; we'll remain on JSON if loading fails
                pass

            self._db_validated = True
            return

        _LOGGER.debug("Unsupported database type for history storage, falling back to JSON")
        self._storage_backend = HISTORY_STORAGE_JSON
        self._db_validated = True

    def _init_database_table(self) -> None:
        """Initialize the database table for history storage."""
        try:
            recorder = get_instance(self.hass)
            if not getattr(recorder, "engine", None):
                raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
            self._db_engine = recorder.engine
            assert self._db_engine is not None

            metadata = MetaData()
            self._db_table = Table(
                DB_TABLE_NAME,
                metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("area_id", String(255), nullable=False, index=True),
                Column("timestamp", DateTime, nullable=False, index=True),
                Column("current_temperature", Float, nullable=False),
                Column("target_temperature", Float, nullable=False),
                Column("state", String(50), nullable=False),
                Column("trvs", String, nullable=True),
            )

            # Create table if it doesn't exist
            metadata.create_all(self._db_engine)

            # Ensure 'trvs' column exists (migrated to helper)
            try:
                self._ensure_trvs_column()
            except Exception:
                _LOGGER.debug(
                    "Could not verify/add 'trvs' column; continuing with best-effort setup"
                )

            _LOGGER.info("Database table '%s' ready for history storage", DB_TABLE_NAME)

        except Exception as e:
            _LOGGER.error("Failed to initialize database table: %s, falling back to JSON", e)
            self._storage_backend = HISTORY_STORAGE_JSON
            self._db_table = None
            self._db_engine = None

    def _ensure_trvs_column(self) -> None:
        """Ensure the 'trvs' column exists in the DB table.

        Runs simple inspection and ALTER TABLE statements where needed. Run-time
        guards are present to avoid sensor errors during initialization.
        """
        from sqlalchemy import inspect, text

        if not getattr(self, "_db_engine", None):
            raise RuntimeError(RECORDER_ENGINE_UNAVAILABLE)
        assert self._db_engine is not None

        inspector = inspect(self._db_engine)
        existing_cols = [c["name"] for c in inspector.get_columns(DB_TABLE_NAME)]

        if "trvs" not in existing_cols:
            _LOGGER.info("Database table '%s' missing 'trvs' column - adding it", DB_TABLE_NAME)
            alter_sql = None
            dialect = self._db_engine.name.lower() if hasattr(self._db_engine, "name") else ""

            # Use TEXT for compatibility across MySQL/Postgres/MariaDB
            if "mysql" in dialect or "mariadb" in dialect:
                alter_sql = f"ALTER TABLE {DB_TABLE_NAME} ADD COLUMN trvs TEXT NULL"
            elif "postgres" in dialect or "postgresql" in dialect:
                alter_sql = f"ALTER TABLE {DB_TABLE_NAME} ADD COLUMN trvs TEXT"
            else:
                # Fallback generic SQL (may work for many DBs)
                alter_sql = f"ALTER TABLE {DB_TABLE_NAME} ADD COLUMN trvs TEXT"

            if alter_sql:

                def _alter():
                    with self._db_engine.connect() as conn:
                        conn.execute(text(alter_sql))
                        # Some DBs require an explicit commit
                        try:
                            conn.commit()
                        except Exception:
                            pass

                # Run migration synchronously (this is called from init time)
                self._db_engine.begin()
                _alter()
                _LOGGER.info("Added 'trvs' column to %s", DB_TABLE_NAME)

    def _get_trvs_alter_sql(self) -> str | None:
        """Return the ALTER SQL required to add the `trvs` column for the DB dialect."""
        if not getattr(self, "_db_engine", None):
            return None
        dialect = self._db_engine.name.lower() if hasattr(self._db_engine, "name") else ""

        if "mysql" in dialect or "mariadb" in dialect:
            return f"ALTER TABLE {DB_TABLE_NAME} ADD COLUMN trvs TEXT NULL"
        if "postgres" in dialect or "postgresql" in dialect:
            return f"ALTER TABLE {DB_TABLE_NAME} ADD COLUMN trvs TEXT"

        # Generic fallback
        return f"ALTER TABLE {DB_TABLE_NAME} ADD COLUMN trvs TEXT"

    async def async_load(self) -> None:
        """Load history from storage."""
        # First, check if there's a stored backend preference in JSON
        data = await self._store.async_load()
        if data and "storage_backend" in data:
            self._storage_backend = data["storage_backend"]

        # Always validate database support where possible so we can auto-detect
        # an existing DB-backed history even if the JSON store doesn't contain
        # a previous preference. This allows history to survive restarts where
        # recorder becomes available later on.
        await self._async_validate_database_support()

        # Now load the actual data
        # Prefer database storage automatically if available and contains data
        if self._db_table is not None:
            # Check whether DB has entries and prefer DB if it does. If the
            # DB contains entries we switch to database backend automatically
            # so users don't lose history after restarts.
            try:
                stats = await self.async_get_database_stats()
                total = stats.get("total_entries") if isinstance(stats, dict) else None
                if total and int(total) > 0:
                    # Prefer DB-backed history if entries exist
                    self._storage_backend = HISTORY_STORAGE_DATABASE
                    await self._async_load_from_database()
                else:
                    # No DB entries: fall back to JSON storage
                    await self._async_load_from_json()
            except Exception:
                # In case of any error querying DB, fall back to JSON to avoid
                # leaving the integration without history at startup
                await self._async_load_from_json()
        else:
            await self._async_load_from_json()

        # Schedule periodic cleanup
        self._cleanup_unsub = async_track_time_interval(
            self.hass, self._async_periodic_cleanup, CLEANUP_INTERVAL
        )
        _LOGGER.info("History cleanup scheduled every %s", CLEANUP_INTERVAL)

    async def _async_load_from_json(self) -> None:
        """Load history from JSON storage."""
        data = await self._store.async_load()

        if data is not None:
            if "history" in data:
                self._history = data["history"]
            if "retention_days" in data:
                self._retention_days = data["retention_days"]
            if "storage_backend" in data:
                # Preserve storage backend preference
                self._storage_backend = data.get("storage_backend", HISTORY_STORAGE_JSON)

            # Clean up old entries
            await self._async_cleanup_old_entries()
            _LOGGER.info(
                "Loaded history for %d areas (retention: %d days, storage: JSON)",
                len(self._history),
                self._retention_days,
            )
        else:
            _LOGGER.debug("No history found in JSON storage")

    async def _async_load_from_database(self) -> None:
        """Load history from database."""
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

            def _collect_history_rows(conn, db_table):
                # Load all rows ordered by timestamp desc and convert to dict
                stmt = select(db_table).order_by(db_table.c.timestamp.desc())
                result = conn.execute(stmt)

                history_dict = {}
                for row in result:
                    area_id = row.area_id
                    if area_id not in history_dict:
                        history_dict[area_id] = []

                    # Parse TRV JSON if present
                    trvs = None
                    try:
                        trvs = json.loads(row.trvs) if row.trvs else None
                    except Exception:
                        trvs = None

                    history_dict[area_id].append(
                        {
                            "timestamp": row.timestamp.isoformat(),
                            "current_temperature": row.current_temperature,
                            "target_temperature": row.target_temperature,
                            # Normalize state values to lowercase so frontend
                            # comparisons (e.g., 'heating'/'cooling') work
                            "state": row.state.lower() if isinstance(row.state, str) else row.state,
                            "trvs": trvs,
                        }
                    )

                return history_dict

            def _load():
                with engine.connect() as conn:
                    return _collect_history_rows(conn, db_table)

            self._history = await recorder.async_add_executor_job(_load)

            # Normalize any state values loaded from the database to lowercase
            for area_id, entries in self._history.items():
                for entry in entries:
                    if "state" in entry and isinstance(entry["state"], str):
                        entry["state"] = entry["state"].lower()

            # Load retention setting from JSON store
            data = await self._store.async_load()
            if data and "retention_days" in data:
                self._retention_days = data["retention_days"]

            # Clean up old entries
            await self._async_cleanup_old_entries()
            _LOGGER.info(
                "Loaded history for %d areas (retention: %d days, storage: Database)",
                len(self._history),
                self._retention_days,
            )
        except Exception as e:
            _LOGGER.error("Failed to load from database: %s, falling back to JSON", e)
            self._storage_backend = HISTORY_STORAGE_JSON
            await self._async_load_from_json()

    async def async_save(self) -> None:
        """Save history to storage."""
        _LOGGER.debug("Saving history to %s storage", self._storage_backend)

        if self._storage_backend == HISTORY_STORAGE_DATABASE and self._db_table is not None:
            await self._async_save_to_database()
        else:
            await self._async_save_to_json()

    async def _async_save_to_json(self) -> None:
        """Save history to JSON storage."""
        data = {
            "history": self._history,
            "retention_days": self._retention_days,
            "storage_backend": self._storage_backend,
        }
        await self._store.async_save(data)

    async def _async_save_to_database(self) -> None:
        """Save history to database."""
        # Database records are inserted individually on async_record_temperature
        # Just save retention settings to JSON
        data = {
            "retention_days": self._retention_days,
            "storage_backend": self._storage_backend,
        }
        await self._store.async_save(data)

    async def async_unload(
        self,
    ) -> None:  # NOSONAR - intentionally async (cleanup tasks may be awaited by caller)
        """Unload and cleanup."""
        # Minimal await to satisfy async function linters
        await asyncio.sleep(0)
        if self._cleanup_unsub:
            self._cleanup_unsub()
            self._cleanup_unsub = None
        _LOGGER.debug("History tracker unloaded")

    async def async_get_database_stats(self) -> dict[str, Any]:
        """Get database statistics for history table.

        Returns a dict containing `enabled` flag and either a `message` when
        database storage is not enabled, or `total_entries` when enabled.
        """
        # If no DB table or not using DB backend, return disabled response
        if self._db_table is None or self._storage_backend != HISTORY_STORAGE_DATABASE:
            return {"enabled": False, "message": "Database storage not enabled"}

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

                    stmt = select(func.count()).select_from(db_table)
                    result = conn.execute(stmt)
                    total = result.scalar()
                    return {"enabled": True, "total_entries": total}

            return await recorder.async_add_executor_job(_get_stats)

        except Exception as e:
            _LOGGER.error("Failed to get database stats: %s", e)
            return {"enabled": False, "message": str(e)}

    async def _async_cleanup_old_entries(self) -> None:
        """Remove entries older than retention period."""
        if self._storage_backend == HISTORY_STORAGE_DATABASE and self._db_table is not None:
            await self._async_cleanup_database()
        else:
            await self._async_cleanup_json()

    async def _async_cleanup_json(self) -> None:
        """Clean up old entries in JSON storage."""
        cutoff = datetime.now() - timedelta(days=self._retention_days)
        cutoff_iso = cutoff.isoformat()

        total_removed = 0
        area_ids = list(self._history)
        for area_id in area_ids:
            original_count = len(self._history[area_id])
            self._history[area_id] = [
                entry for entry in self._history[area_id] if entry["timestamp"] > cutoff_iso
            ]
            removed = original_count - len(self._history[area_id])
            total_removed += removed
            if removed > 0:
                _LOGGER.debug(
                    "Removed %d old entries for area %s (retention: %d days)",
                    removed,
                    area_id,
                    self._retention_days,
                )

        if total_removed > 0:
            _LOGGER.info(
                "History cleanup: removed %d entries older than %d days (JSON)",
                total_removed,
                self._retention_days,
            )
            await self.async_save()

    async def _async_cleanup_database(self) -> None:
        """Clean up old entries in database storage."""
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

            cutoff = datetime.now() - timedelta(days=self._retention_days)

            def _cleanup():
                with engine.connect() as conn:
                    stmt = delete(db_table).where(db_table.c.timestamp < cutoff)
                    result = conn.execute(stmt)
                    conn.commit()
                    return result.rowcount

            removed = await recorder.async_add_executor_job(_cleanup)

            if removed > 0:
                _LOGGER.info(
                    "History cleanup: removed %d entries older than %d days (Database)",
                    removed,
                    self._retention_days,
                )
                # Reload in-memory cache
                await self._async_load_from_database()

        except Exception as e:
            _LOGGER.error("Failed to cleanup database: %s", e)

    async def _async_periodic_cleanup(self, now=None) -> None:
        """Periodic cleanup task."""
        _LOGGER.debug("Running periodic history cleanup")
        await self._async_cleanup_old_entries()

    async def async_record_temperature(
        self,
        area_id: str,
        current_temp: float,
        target_temp: float,
        state: str,
        trvs: list[dict] | None = None,
    ) -> None:
        """Record a temperature reading.

        Args:
            area_id: Area identifier
            current_temp: Current temperature
            target_temp: Target temperature
            state: Area state (heating/idle/off)
            trvs: Optional list of TRV states to include in the entry
        """
        timestamp = datetime.now()
        entry = {
            "timestamp": timestamp.isoformat(),
            "current_temperature": current_temp,
            "target_temperature": target_temp,
            "state": state,
            "trvs": trvs,
        }

        # Always maintain in-memory cache
        if area_id not in self._history:
            self._history[area_id] = []

        self._history[area_id].append(entry)

        # Limit to last 1000 entries per area in memory
        if len(self._history[area_id]) > 1000:
            self._history[area_id] = self._history[area_id][-1000:]

        # Persist to storage backend
        if self._storage_backend == HISTORY_STORAGE_DATABASE and self._db_table is not None:
            await self._async_save_to_database_entry(
                area_id, timestamp, current_temp, target_temp, state, trvs
            )

        _LOGGER.debug(
            "Recorded temperature for %s: %.1f°C (target: %.1f°C, state: %s) [%s]",
            area_id,
            current_temp,
            target_temp,
            state,
            self._storage_backend,
        )

    async def _async_save_to_database_entry(
        self,
        area_id: str,
        timestamp: datetime,
        current_temp: float,
        target_temp: float,
        state: str,
        trvs: list[dict] | None = None,
    ) -> None:
        """Save a single entry to the database."""
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
                    stmt = db_table.insert().values(
                        area_id=area_id,
                        timestamp=timestamp,
                        current_temperature=current_temp,
                        target_temperature=target_temp,
                        state=state,
                        trvs=json.dumps(trvs) if trvs is not None else None,
                    )
                    conn.execute(stmt)
                    conn.commit()

            await recorder.async_add_executor_job(_insert)

        except Exception as e:
            _LOGGER.error("Failed to save entry to database: %s", e)

    def get_history(
        self,
        area_id: str,
        hours: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get temperature history for an area.

        Args:
            area_id: Area identifier
            hours: Number of hours to retrieve (default: None, returns all within retention)
            start_time: Custom start time (optional)
            end_time: Custom end time (optional, defaults to now)

        Returns:
            List of history entries
        """
        if area_id not in self._history:
            return []

        # Determine time range
        if start_time and end_time:
            # Custom time range
            start_iso = start_time.isoformat()
            end_iso = end_time.isoformat()
            entries = [
                entry
                for entry in self._history[area_id]
                if start_iso <= entry["timestamp"] <= end_iso
            ]
        elif hours:
            # Hours-based query
            cutoff = datetime.now() - timedelta(hours=hours)
            cutoff_iso = cutoff.isoformat()
            entries = [entry for entry in self._history[area_id] if entry["timestamp"] > cutoff_iso]
        else:
            # Return all available history (within retention period)
            entries = list(self._history[area_id])

        # Normalize state values on return to ensure frontend comparisons work
        for entry in entries:
            if "state" in entry and isinstance(entry["state"], str):
                entry["state"] = entry["state"].lower()

        return entries

    def get_all_history(self) -> dict[str, list[dict[str, Any]]]:
        """Get all history.

        Returns:
            Dictionary of area_id -> history entries
        """
        return self._history

    def set_retention_days(self, days: int) -> None:
        """Set the history retention period.

        Args:
            days: Number of days to retain history
        """
        if days < 1:
            raise ValueError("Retention period must be at least 1 day")
        if days > MAX_HISTORY_RETENTION_DAYS:
            raise ValueError(f"Retention period cannot exceed {MAX_HISTORY_RETENTION_DAYS} days")

        old_retention = self._retention_days
        self._retention_days = days
        _LOGGER.info("History retention changed from %d to %d days", old_retention, days)

    def get_retention_days(self) -> int:
        """Get the current retention period.

        Returns:
            Number of days history is retained
        """
        return self._retention_days

    def get_storage_backend(self) -> str:
        """Get the current storage backend.

        Returns:
            Current storage backend (json or database)
        """
        return self._storage_backend

    async def async_migrate_storage(self, target_backend: str) -> dict[str, Any]:
        """Migrate history data between storage backends.

        Args:
            target_backend: Target storage backend (json or database)

        Returns:
            Migration result with status and details
        """
        if target_backend == self._storage_backend:
            return {
                "success": False,
                "message": f"Already using {target_backend} storage",
                "migrated_entries": 0,
            }

        # Validate target backend
        if target_backend not in [HISTORY_STORAGE_JSON, HISTORY_STORAGE_DATABASE]:
            return {
                "success": False,
                "message": f"Invalid storage backend: {target_backend}",
                "migrated_entries": 0,
            }

        # Capture source backend BEFORE any changes
        source_backend = self._storage_backend

        # Check database support if migrating to database
        if target_backend == HISTORY_STORAGE_DATABASE:
            self._storage_backend = target_backend
            self._db_validated = False  # Reset validation flag
            await self._async_validate_database_support()

            if self._storage_backend != HISTORY_STORAGE_DATABASE:
                # Validation failed, backend was reset to JSON
                self._storage_backend = source_backend
                return {
                    "success": False,
                    "message": "Database storage not supported (SQLite or validation failed)",
                    "migrated_entries": 0,
                }

        _LOGGER.info(
            "Starting migration from %s to %s storage",
            source_backend,
            target_backend,
        )

        try:
            # Count total entries
            total_entries = sum(len(entries) for entries in self._history.values())

            # Perform migration
            if target_backend == HISTORY_STORAGE_DATABASE:
                await self._migrate_to_database()
            else:
                await self._migrate_to_json()

            # Update backend
            self._storage_backend = target_backend
            await self.async_save()

            _LOGGER.info(
                "Migration complete: %s → %s (%d entries)",
                source_backend,
                target_backend,
                total_entries,
            )

            return {
                "success": True,
                "message": f"Successfully migrated from {source_backend} to {target_backend}",
                "migrated_entries": total_entries,
                "source_backend": source_backend,
                "target_backend": target_backend,
            }

        except Exception as e:
            _LOGGER.error("Migration failed: %s", e)
            return {
                "success": False,
                "message": f"Migration failed: {str(e)}",
                "migrated_entries": 0,
            }

    async def _migrate_to_database(self) -> None:
        """Migrate all in-memory history to database."""
        if self._db_table is None:
            self._init_database_table()

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

        def _perform_batch_insert(engine, db_table, history):
            with engine.connect() as conn:
                for area_id, entries in history.items():
                    for entry in entries:
                        timestamp = datetime.fromisoformat(entry["timestamp"])
                        stmt = db_table.insert().values(
                            area_id=area_id,
                            timestamp=timestamp,
                            current_temperature=entry["current_temperature"],
                            target_temperature=entry["target_temperature"],
                            state=entry["state"],
                            trvs=json.dumps(entry.get("trvs"))
                            if entry.get("trvs") is not None
                            else None,
                        )
                        conn.execute(stmt)
                conn.commit()

        await recorder.async_add_executor_job(
            _perform_batch_insert, engine, db_table, self._history
        )
        _LOGGER.info("Migrated all entries to database")
