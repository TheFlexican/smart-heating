"""Import/Export API handlers for Smart Heating."""

import asyncio
import json
import logging

import aiofiles
from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ...storage.config_manager import ConfigManager

_LOGGER = logging.getLogger(__name__)

ERROR_INTERNAL = "Internal server error"


async def handle_export_config(_hass: HomeAssistant, config_manager: ConfigManager) -> web.Response:
    """Export configuration as JSON file.

    Args:
        hass: Home Assistant instance
        config_manager: Config manager instance

    Returns:
        JSON file download response
    """
    try:
        # Export configuration
        config_data = await config_manager.async_export_config()

        # Convert to JSON string with nice formatting
        json_str = json.dumps(config_data, indent=2, ensure_ascii=False)

        # Create filename with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_heating_backup_{timestamp}.json"

        # Return as downloadable file
        return web.Response(
            body=json_str.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except (HomeAssistantError, json.JSONDecodeError) as err:
        _LOGGER.error("Failed to export configuration: %s", err)
        return web.json_response({"error": f"Export failed: {str(err)}"}, status=500)


async def handle_import_config(
    _hass: HomeAssistant, config_manager: ConfigManager, data: dict
) -> web.Response:
    """Import configuration from JSON data.

    Args:
        hass: Home Assistant instance
        config_manager: Config manager instance
        data: Configuration data or upload info

    Returns:
        JSON response with import results
    """
    try:
        # Data can come from either direct JSON or file upload
        config_data = data

        # Import configuration (creates automatic backup)
        changes = await config_manager.async_import_config(config_data, create_backup=True)

        _LOGGER.info("Configuration imported successfully: %s", changes)

        return web.json_response(
            {
                "success": True,
                "message": "Configuration imported successfully",
                "changes": changes,
            }
        )

    except ValueError as err:
        _LOGGER.exception("Invalid configuration data")
        return web.json_response({"error": f"Invalid configuration: {str(err)}"}, status=400)
    except (HomeAssistantError, json.JSONDecodeError) as err:
        _LOGGER.exception("Failed to import configuration")
        return web.json_response({"error": str(err), "message": ERROR_INTERNAL}, status=500)


async def handle_validate_config(
    _hass: HomeAssistant, config_manager: ConfigManager, data: dict
) -> web.Response:
    """Validate configuration without importing.

    Args:
        hass: Home Assistant instance
        config_manager: Config manager instance
        data: Configuration data to validate

    Returns:
        JSON response with validation results
    """
    try:
        # Validate structure
        config_manager._validate_import_data(data)

        # Count what would be imported
        existing_areas = set(config_manager.area_manager.get_all_areas().keys())
        imported_areas = set(data.get("areas", {}).keys())

        areas_to_create = imported_areas - existing_areas
        areas_to_update = imported_areas & existing_areas

        preview = {
            "valid": True,
            "version": data.get("version"),
            "export_date": data.get("export_date"),
            "areas_to_create": len(areas_to_create),
            "areas_to_update": len(areas_to_update),
            "global_settings_included": "global_settings" in data,
            "vacation_mode_included": "vacation_mode" in data,
        }

        # Yield once to satisfy async checks
        await asyncio.sleep(0)
        return web.json_response(preview)

    except ValueError as err:
        return web.json_response({"valid": False, "error": str(err)}, status=400)
    except (HomeAssistantError, json.JSONDecodeError) as err:
        _LOGGER.error("Failed to validate configuration: %s", err)
        return web.json_response(
            {"valid": False, "error": f"Validation failed: {str(err)}"}, status=500
        )


async def handle_list_backups(_hass: HomeAssistant, config_manager: ConfigManager) -> web.Response:
    """List available backup files.

    Args:
        hass: Home Assistant instance
        config_manager: Config manager instance

    Returns:
        JSON response with list of backups
    """
    await asyncio.sleep(0)  # Minimal async operation to satisfy async requirement
    try:
        backup_dir = config_manager.backup_dir

        if not backup_dir.exists():
            return web.json_response({"backups": []})

        backups = []
        for backup_file in sorted(backup_dir.glob("backup_*.json"), reverse=True):
            stat = backup_file.stat()
            backups.append(
                {
                    "filename": backup_file.name,
                    "size": stat.st_size,
                    "created": stat.st_mtime,
                }
            )

        return web.json_response({"backups": backups})

    except (HomeAssistantError, json.JSONDecodeError) as err:
        _LOGGER.exception("Failed to list backups")
        return web.json_response({"error": str(err), "message": ERROR_INTERNAL}, status=500)


async def handle_restore_backup(
    _hass: HomeAssistant, config_manager: ConfigManager, backup_filename: str
) -> web.Response:
    """Restore from a specific backup file.

    Args:
        hass: Home Assistant instance
        config_manager: Config manager instance
        backup_filename: Name of backup file to restore

    Returns:
        JSON response with restore results
    """
    try:
        backup_file = config_manager.backup_dir / backup_filename

        if not backup_file.exists():
            return web.json_response(
                {"error": f"Backup file not found: {backup_filename}"}, status=404
            )

        # Load backup data using aiofiles to avoid blocking the event loop
        async with aiofiles.open(backup_file, "r", encoding="utf-8") as f:
            content = await f.read()
            config_data = json.loads(content)

        # Import configuration (creates another backup before restore)
        changes = await config_manager.async_import_config(config_data, create_backup=True)

        _LOGGER.info("Backup restored successfully: %s", backup_filename)

        return web.json_response(
            {
                "success": True,
                "message": f"Backup {backup_filename} restored successfully",
                "changes": changes,
            }
        )

    except (HomeAssistantError, json.JSONDecodeError) as err:
        _LOGGER.exception("Failed to restore backup")
        return web.json_response({"error": str(err), "message": ERROR_INTERNAL}, status=500)
