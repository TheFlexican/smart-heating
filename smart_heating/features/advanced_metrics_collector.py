"""Advanced metrics collection for Smart Heating dashboard."""

# Database and recorder integrations are exercised in integration tests; exclude from unit test coverage
# pragma: no cover

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from homeassistant.components.recorder import get_instance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    Table,
    Text,
    delete,
    select,
)

_LOGGER = logging.getLogger(__name__)

# Domain constant for data storage
DOMAIN = "smart_heating"

# Collection interval (5 minutes)
COLLECTION_INTERVAL = timedelta(minutes=5)
# Data retention (30 days)
RETENTION_DAYS = 30
# Database table name
METRICS_TABLE_NAME = "smart_heating_advanced_metrics"


class AdvancedMetricsCollector:
    """Collect and store advanced heating system metrics."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the metrics collector.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._db_table = None
        self._db_engine = None
        self._collection_unsub = None
        self._cleanup_unsub = None
        self._initialized = False

    async def async_setup(self) -> bool:
        """Set up the metrics collector.

        Returns:
            True if setup successful, False otherwise
        """
        _LOGGER.debug("Advanced metrics collector async_setup called")
        try:
            # Initialize database table
            _LOGGER.debug("Attempting to initialize advanced metrics database...")
            if not await self._async_init_database():
                _LOGGER.info("Advanced metrics collection disabled - database not available")
                return False

            _LOGGER.debug("Advanced metrics database initialized successfully")

            # Schedule periodic collection every 5 minutes
            self._collection_unsub = async_track_time_interval(
                self.hass, self._async_collect_metrics, COLLECTION_INTERVAL
            )
            _LOGGER.debug("Advanced metrics collection scheduled every 5 minutes")

            # Schedule daily cleanup at 3 AM
            self._cleanup_unsub = async_track_time_interval(
                self.hass, self._async_cleanup_old_metrics, timedelta(hours=24)
            )

            # Mark as initialized BEFORE collecting initial metrics
            self._initialized = True
            _LOGGER.debug("Advanced metrics collector marked as initialized")

            # Collect initial metrics
            _LOGGER.debug("Collecting initial advanced metrics (initial)")
            await self._async_collect_metrics(None)
            _LOGGER.debug("Initial advanced metrics collected")

            _LOGGER.info("Advanced metrics collector initialized (5-minute interval)")
            return True

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("❌ Failed to setup advanced metrics collector: %s", err, exc_info=True)
            return False

    async def _async_init_database(self) -> bool:  # NOSONAR
        """Initialize the database table.

        Returns:
            True if successful, False otherwise
        """
        try:
            recorder = get_instance(self.hass)
            if not recorder:
                _LOGGER.debug("Recorder not available for advanced metrics")
                return False

            db_url = str(recorder.db_url)

            # Only support MariaDB/MySQL and PostgreSQL
            if "sqlite" in db_url.lower():
                _LOGGER.debug("SQLite not supported for advanced metrics")
                return False

            if not any(
                db in db_url.lower() for db in ["mysql", "mariadb", "postgresql", "postgres"]
            ):
                _LOGGER.debug("Unsupported database type for advanced metrics")
                return False

            self._db_engine = recorder.engine

            metadata = MetaData()
            self._db_table = Table(
                METRICS_TABLE_NAME,
                metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("timestamp", DateTime, nullable=False, index=True),
                # Global metrics
                Column("outdoor_temp", Float, nullable=True),
                Column("boiler_flow_temp", Float, nullable=True),
                Column("boiler_return_temp", Float, nullable=True),
                Column("boiler_setpoint", Float, nullable=True),
                Column("modulation_level", Float, nullable=True),
                Column("flame_on", Boolean, nullable=True),
                # Per-area metrics stored as JSON
                Column("area_metrics", Text, nullable=True),  # JSON string
            )

            # Create table if it doesn't exist
            metadata.create_all(self._db_engine)
            _LOGGER.info("Advanced metrics table '%s' ready", METRICS_TABLE_NAME)
            return True

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Failed to initialize metrics database: %s", err, exc_info=True)
            return False

    async def _async_collect_metrics(self, _now: Optional[datetime]) -> None:
        """Collect current metrics and store in database.

        Args:
            _now: Current time (unused, required by async_track_time_interval)
        """
        _LOGGER.debug("_async_collect_metrics called")
        try:
            if not self._initialized or self._db_table is None:
                _LOGGER.debug("Skipping advanced metrics collection - not initialized or no table")
                return

            # Get area manager and coordinator
            area_manager = self.hass.data.get(DOMAIN, {}).get("area_manager")
            if not area_manager:
                _LOGGER.debug(
                    "No area_manager found in hass.data - components still initializing, will retry on next cycle"
                )
                return

            _LOGGER.debug("Collecting OpenTherm metrics")
            opentherm_metrics = await self._async_get_opentherm_metrics()
            _LOGGER.debug("OpenTherm metrics: %s", opentherm_metrics)

            # Collect per-area metrics
            _LOGGER.debug("Collecting area metrics...")
            area_metrics = await self._async_get_area_metrics(area_manager)
            _LOGGER.debug("Area metrics count: %d", len(area_metrics))

            # Insert into database
            _LOGGER.debug("Inserting metrics into database")
            await self._async_insert_metrics(opentherm_metrics, area_metrics)
            _LOGGER.info("Advanced metrics successfully inserted into database")

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("❌ Error collecting metrics: %s", err, exc_info=True)

    async def _async_get_opentherm_metrics(self) -> dict[str, Any]:  # NOSONAR
        """Get current OpenTherm gateway metrics.

        Returns:
            Dictionary of OpenTherm metrics
        """
        metrics = {}

        try:
            # Try to get outdoor temperature from weather entity
            weather_state = self.hass.states.get("weather.forecast_thuis")
            if weather_state:
                metrics["outdoor_temp"] = weather_state.attributes.get("temperature")

            # Get OpenTherm sensor values
            sensor_mappings = {
                "boiler_flow_temp": [
                    "sensor.opentherm_gateway_otgw_otgw_boiler_flow_water_temperature",
                    "sensor.opentherm_ketel_centrale_verwarming_1_watertemperatuur",
                ],
                "boiler_return_temp": [
                    "sensor.opentherm_gateway_otgw_otgw_return_water_temperature",
                    "sensor.opentherm_ketel_temperatuur_retourwater",
                ],
                "boiler_setpoint": [
                    "sensor.opentherm_gateway_otgw_otgw_control_setpoint",
                    "sensor.opentherm_ketel_regel_instelpunt_1",
                ],
                "modulation_level": [
                    "sensor.opentherm_gateway_otgw_otgw_relative_modulation_level",
                    "sensor.opentherm_ketel_relatief_modulatieniveau",
                ],
            }

            for metric_key, entity_ids in sensor_mappings.items():
                for entity_id in entity_ids:
                    state = self.hass.states.get(entity_id)
                    if state and state.state not in ("unknown", "unavailable"):
                        try:
                            metrics[metric_key] = float(state.state)
                            break
                        except (ValueError, TypeError):
                            continue

            # Get flame status
            flame_entities = [
                "binary_sensor.opentherm_ketel_vlam",
                "binary_sensor.opentherm_gateway_flame",
            ]
            for entity_id in flame_entities:
                state = self.hass.states.get(entity_id)
                if state:
                    metrics["flame_on"] = state.state == "on"
                    break

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Error getting OpenTherm metrics: %s", err)

        return metrics

    async def _async_get_area_metrics(self, area_manager) -> dict[str, Any]:  # NOSONAR
        """Get current per-area metrics.

        Args:
            area_manager: AreaManager instance

        Returns:
            Dictionary of area metrics
        """
        area_metrics = {}

        try:
            for area_id, area in area_manager.get_all_areas().items():
                area_metrics[area_id] = {
                    "current_temp": area.current_temperature,
                    "target_temp": area.target_temperature,
                    "state": area.state,
                    "heating_type": getattr(area, "heating_type", "radiator"),
                    "heating_curve_coefficient": getattr(area, "heating_curve_coefficient", None),
                    "hysteresis_override": getattr(area, "hysteresis_override", None),
                }

                # Include thermostat failure/backoff state if available from climate controller
                try:
                    climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
                    if climate_controller and hasattr(area, "get_thermostats"):
                        device_handler = getattr(climate_controller, "device_handler", None)
                        if device_handler:
                            failures: dict[str, dict] = {}
                            for tid in area.get_thermostats():
                                try:
                                    st = device_handler.get_thermostat_failure_state(tid)
                                except Exception:
                                    st = None
                                if st:
                                    failures[tid] = st
                            if failures:
                                area_metrics[area_id]["thermostat_failures"] = failures
                except Exception:
                    # Non-critical; log debug and continue
                    _LOGGER.debug("Error collecting thermostat failure state for area %s", area_id)

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Error getting area metrics: %s", err)

        return area_metrics

    async def _async_insert_metrics(
        self, opentherm_metrics: dict[str, Any], area_metrics: dict[str, Any]
    ) -> None:
        """Insert metrics into database.

        Args:
            opentherm_metrics: Global OpenTherm metrics
            area_metrics: Per-area metrics
        """
        if self._db_engine is None or self._db_table is None:
            return

        try:
            # Prepare insert data
            insert_data = {
                "timestamp": datetime.now(),
                "outdoor_temp": opentherm_metrics.get("outdoor_temp"),
                "boiler_flow_temp": opentherm_metrics.get("boiler_flow_temp"),
                "boiler_return_temp": opentherm_metrics.get("boiler_return_temp"),
                "boiler_setpoint": opentherm_metrics.get("boiler_setpoint"),
                "modulation_level": opentherm_metrics.get("modulation_level"),
                "flame_on": opentherm_metrics.get("flame_on"),
                "area_metrics": json.dumps(area_metrics) if area_metrics else None,
            }

            # Execute insert in recorder executor
            recorder = get_instance(self.hass)
            await recorder.async_add_executor_job(self._insert_metrics_sync, insert_data)

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error inserting metrics: %s", err, exc_info=True)

    def _insert_metrics_sync(self, insert_data: dict[str, Any]) -> None:
        """Synchronously insert metrics (runs in executor).

        Args:
            insert_data: Data to insert
        """
        with self._db_engine.begin() as conn:
            conn.execute(self._db_table.insert().values(**insert_data))

    async def _async_cleanup_old_metrics(self, _now: Optional[datetime]) -> None:
        """Clean up metrics older than retention period.

        Args:
            _now: Current time (unused, required by async_track_time_interval)
        """
        if self._db_engine is None or self._db_table is None:
            return

        try:
            cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)

            recorder = get_instance(self.hass)
            deleted = await recorder.async_add_executor_job(
                self._cleanup_old_metrics_sync, cutoff_date
            )

            if deleted > 0:
                _LOGGER.info("Cleaned up %d old advanced metrics records", deleted)

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error cleaning up old metrics: %s", err, exc_info=True)

    def _cleanup_old_metrics_sync(self, cutoff_date: datetime) -> int:
        """Synchronously delete old metrics (runs in executor).

        Args:
            cutoff_date: Delete records older than this date

        Returns:
            Number of deleted records
        """
        with self._db_engine.begin() as conn:
            result = conn.execute(
                delete(self._db_table).where(self._db_table.c.timestamp < cutoff_date)
            )
            return result.rowcount

    async def async_get_metrics(
        self, days: int | None = 7, minutes: int | None = None, area_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get metrics for specified time range.

        Args:
            days: Number of days of history to retrieve (1, 3, 7, or 30). Used when `minutes` is None.
            minutes: Optional minutes-based window (1,2,3,5) for short-range queries.
            area_id: Optional area ID to filter metrics

        Returns:
            List of metric records
        """
        if self._db_engine is None or self._db_table is None:
            return []

        try:
            if minutes is not None:
                start_date = datetime.now() - timedelta(minutes=minutes)
            else:
                # default to days if minutes not provided
                start_date = datetime.now() - timedelta(days=days or 7)

            recorder = get_instance(self.hass)
            results = await recorder.async_add_executor_job(
                self._get_metrics_sync, start_date, area_id
            )

            return results

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error retrieving metrics: %s", err, exc_info=True)
            return []

    def _get_metrics_sync(
        self, start_date: datetime, area_id: Optional[str]
    ) -> list[dict[str, Any]]:
        """Synchronously retrieve metrics (runs in executor).

        Args:
            start_date: Start date for query
            area_id: Optional area ID filter

        Returns:
            List of metric records
        """
        with self._db_engine.connect() as conn:
            stmt = (
                select(self._db_table)
                .where(self._db_table.c.timestamp >= start_date)
                .order_by(self._db_table.c.timestamp)
            )

            result = conn.execute(stmt)
            rows = result.fetchall()

            metrics = []
            for row in rows:
                metric = {
                    "timestamp": row.timestamp.isoformat(),
                    "outdoor_temp": row.outdoor_temp,
                    "boiler_flow_temp": row.boiler_flow_temp,
                    "boiler_return_temp": row.boiler_return_temp,
                    "boiler_setpoint": row.boiler_setpoint,
                    "modulation_level": row.modulation_level,
                    "flame_on": row.flame_on,
                }

                # Parse area metrics JSON
                if row.area_metrics:
                    try:
                        area_metrics_dict = json.loads(row.area_metrics)
                        # If filtering by area_id, only include that area's data
                        if area_id:
                            if area_id in area_metrics_dict:
                                metric["area_metrics"] = {area_id: area_metrics_dict[area_id]}
                        else:
                            metric["area_metrics"] = area_metrics_dict
                    except json.JSONDecodeError:
                        metric["area_metrics"] = {}

                metrics.append(metric)

            return metrics

    async def async_stop(self) -> None:  # NOSONAR
        """Stop the metrics collector."""
        if self._collection_unsub:
            self._collection_unsub()
            self._collection_unsub = None

        if self._cleanup_unsub:
            self._cleanup_unsub()
            self._cleanup_unsub = None

        _LOGGER.info("Advanced metrics collector stopped")
