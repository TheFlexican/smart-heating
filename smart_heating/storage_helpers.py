"""Helpers to clear Smart Heating persistent storage on uninstall.

This module implements all-or-nothing deletion helpers used by
`async_remove_entry` when `keep_data_on_uninstall` is False.

Per project rules this implementation will remove .storage keys, remove
integration-created storage directory (backups/logs) and DROP custom DB
tables if a recorder DB is available.
"""

from __future__ import annotations

import logging
import re
import shutil
from typing import Iterable

from homeassistant.components.recorder import get_instance as get_recorder_instance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from sqlalchemy import text

from .const import DOMAIN, STORAGE_VERSION
from .exceptions import StorageError

_LOGGER = logging.getLogger(__name__)


async def clear_all_persistent_data(hass: HomeAssistant) -> None:
    """Clear all persistent data created by the Smart Heating integration.

    This performs the following steps:
    - Remove Store JSON files for main config, history and events
    - Remove integration storage directory (backups, logs, etc.) under .storage/<DOMAIN>
    - Drop custom recorder/SQL tables if recorder is available
    """
    # Remove HA Store keys
    await _async_remove_store_keys(
        hass,
        [
            f"{DOMAIN}_storage",
            "smart_heating_history",
            "smart_heating_events",
        ],
    )

    # Remove integration storage directory under HA config (.storage/<domain>)
    storage_dir = hass.config.path(".storage", DOMAIN)
    await hass.async_add_executor_job(_remove_path, storage_dir)

    # Drop custom DB tables if recorder available
    await _async_drop_recorder_tables(
        hass,
        [
            "smart_heating_history",
            "smart_heating_events",
            "smart_heating_advanced_metrics",
        ],
    )


async def _async_remove_store_keys(hass: HomeAssistant, keys: Iterable[str]) -> None:
    """Remove store keys using Home Assistant Store helper."""
    for key in keys:
        try:
            store = Store(hass, STORAGE_VERSION, key)
            await store.async_remove()
            _LOGGER.info("Removed store key: %s", key)
        except (StorageError, OSError, RuntimeError) as err:
            _LOGGER.debug("Failed to remove store key %s: %s", key, err)


def _remove_path(path: str) -> None:
    """Synchronously remove a filesystem path (file or directory)."""
    try:
        shutil.rmtree(path)
        _LOGGER.info("Removed storage directory: %s", path)
    except FileNotFoundError:
        _LOGGER.debug("Storage directory not found: %s", path)
    except (StorageError, OSError, RuntimeError) as err:
        _LOGGER.warning("Failed to remove storage directory %s: %s", path, err)


def _validate_table_names(table_names: Iterable[str]) -> list[str]:
    """Validate table names for safe SQL usage."""
    identifier_re = re.compile(r"^[A-Za-z_]\w*$")
    valid_tables: list[str] = []

    for tbl in table_names:
        if not _is_valid_table_name(tbl, identifier_re):
            continue
        valid_tables.append(tbl)

    return valid_tables


def _is_valid_table_name(tbl, identifier_re) -> bool:
    """Check if a table name is valid for SQL operations."""
    if not isinstance(tbl, str):
        _LOGGER.warning("Skipping invalid table name when attempting drop: %s", tbl)
        return False
    if not identifier_re.match(tbl):
        _LOGGER.warning("Skipping invalid table name when attempting drop: %s", tbl)
        return False
    if len(tbl) > 255:
        _LOGGER.warning("Skipping table name (too long): %s", tbl)
        return False
    return True


async def _async_drop_recorder_tables(hass: HomeAssistant, table_names: Iterable[str]) -> None:
    """Drop custom recorder tables via the recorder engine in executor."""
    try:
        recorder = get_recorder_instance(hass)
        if not recorder or not getattr(recorder, "engine", None):
            _LOGGER.debug("Recorder engine not available; skipping table drops")
            return

        valid_tables = _validate_table_names(table_names)
        if not valid_tables:
            _LOGGER.debug("No valid recorder table names to drop; skipping")
            return

        await _execute_table_drops(hass, recorder, valid_tables)
    except (StorageError, OSError, RuntimeError) as err:
        _LOGGER.warning("Error while attempting to drop recorder tables: %s", err)


async def _execute_table_drops(hass: HomeAssistant, recorder, valid_tables: list[str]) -> None:
    """Execute the table drop operations via the recorder executor."""
    engine = recorder.engine

    def _drop():
        with engine.begin() as conn:
            for tbl in valid_tables:
                _drop_single_table(conn, tbl)

    if hasattr(recorder, "async_add_executor_job"):
        await recorder.async_add_executor_job(_drop)
    else:
        _LOGGER.warning(
            "Recorder executor unavailable; falling back to hass.async_add_executor_job("
            "tests/CI only). This may trigger recorder warnings in Home Assistant."
        )
        await hass.async_add_executor_job(_drop)


def _drop_single_table(conn, tbl: str) -> None:
    """Drop a single table, logging the result."""
    try:
        sql = text(f"DROP TABLE IF EXISTS {tbl}")
        conn.execute(sql)
        _LOGGER.info("Dropped table (if existed): %s", tbl)
    except (StorageError, OSError, RuntimeError) as err:
        _LOGGER.warning("Failed to drop table %s: %s", tbl, err)
