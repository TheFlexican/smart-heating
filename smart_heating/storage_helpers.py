"""Helpers to clear Smart Heating persistent storage on uninstall.

This module implements all-or-nothing deletion helpers used by
`async_remove_entry` when `keep_data_on_uninstall` is False.

Per project rules this implementation will remove .storage keys, remove
integration-created storage directory (backups/logs) and DROP custom DB
tables if a recorder DB is available.
"""

from __future__ import annotations

import logging
import shutil
from typing import Iterable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from homeassistant.components.recorder import get_instance as get_recorder_instance
from sqlalchemy import text
import re

from .const import STORAGE_VERSION, DOMAIN

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
        except Exception as err:
            _LOGGER.debug("Failed to remove store key %s: %s", key, err)


def _remove_path(path: str) -> None:
    """Synchronously remove a filesystem path (file or directory)."""
    try:
        shutil.rmtree(path)
        _LOGGER.info("Removed storage directory: %s", path)
    except FileNotFoundError:
        _LOGGER.debug("Storage directory not found: %s", path)
    except Exception as err:
        _LOGGER.warning("Failed to remove storage directory %s: %s", path, err)


async def _async_drop_recorder_tables(hass: HomeAssistant, table_names: Iterable[str]) -> None:
    """Drop custom recorder tables via the recorder engine in executor.

    Uses `DROP TABLE IF EXISTS <table>` for each table.
    """
    try:
        recorder = get_recorder_instance(hass)
        if not recorder or not getattr(recorder, "engine", None):
            _LOGGER.debug("Recorder engine not available; skipping table drops")
            return

        engine = recorder.engine

        # Validate table names to avoid SQL injection via table name.
        # Accept only identifiers: start with letter or underscore, then letters/numbers/underscores.
        identifier_re = re.compile(r"^[A-Za-z_]\w*$")

        valid_tables = []
        for tbl in table_names:
            if not isinstance(tbl, str) or not identifier_re.match(tbl):
                _LOGGER.warning("Skipping invalid table name when attempting drop: %s", tbl)
                continue
            # Protect against excessively long names
            if len(tbl) > 255:
                _LOGGER.warning("Skipping table name (too long): %s", tbl)
                continue
            valid_tables.append(tbl)

        if not valid_tables:
            _LOGGER.debug("No valid recorder table names to drop; skipping")
            return

        def _drop():
            # Use begin() to ensure transactional semantics where supported
            with engine.begin() as conn:
                for tbl in valid_tables:
                    try:
                        # Safe because tbl has been validated to be a simple identifier
                        sql = text(f"DROP TABLE IF EXISTS {tbl}")
                        conn.execute(sql)
                        _LOGGER.info("Dropped table (if existed): %s", tbl)
                    except Exception as err:
                        _LOGGER.warning("Failed to drop table %s: %s", tbl, err)

        await hass.async_add_executor_job(_drop)

    except Exception as err:
        _LOGGER.warning("Error while attempting to drop recorder tables: %s", err)
