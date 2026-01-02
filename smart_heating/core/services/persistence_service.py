"""Configuration persistence service."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ...const import (
    DEFAULT_FROST_PROTECTION_TEMP,
    DEFAULT_TRV_HEATING_TEMP,
    DEFAULT_TRV_IDLE_TEMP,
    DEFAULT_TRV_TEMP_OFFSET,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class PersistenceService:
    """Handles loading and saving configuration to persistent storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize persistence service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    async def async_load(self) -> dict[str, Any] | None:
        """Load configuration from storage.

        Returns:
            Configuration dictionary or None if no data exists
        """
        _LOGGER.debug("Loading configuration from storage")
        data = await self._store.async_load()

        if data is not None:
            _LOGGER.info("Loaded configuration from storage")
        else:
            _LOGGER.debug("No configuration found in storage")

        return data

    async def async_save(self, data: dict[str, Any]) -> None:
        """Save configuration to storage.

        Args:
            data: Configuration dictionary to save
        """
        _LOGGER.debug("Saving configuration to storage")
        await self._store.async_save(data)
        _LOGGER.info("Saved configuration to storage")

    def load_global_config(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract global configuration from loaded data.

        Args:
            data: Loaded configuration dictionary

        Returns:
            Dictionary of global configuration values
        """
        return {
            "opentherm_gateway_id": data.get("opentherm_gateway_id"),
            "trv_heating_temp": data.get("trv_heating_temp", DEFAULT_TRV_HEATING_TEMP),
            "trv_idle_temp": data.get("trv_idle_temp", DEFAULT_TRV_IDLE_TEMP),
            "trv_temp_offset": data.get("trv_temp_offset", DEFAULT_TRV_TEMP_OFFSET),
            "frost_protection_enabled": data.get("frost_protection_enabled", False),
            "frost_protection_temp": data.get(
                "frost_protection_temp", DEFAULT_FROST_PROTECTION_TEMP
            ),
            "hysteresis": data.get("hysteresis", 0.5),
            "hide_devices_panel": data.get("hide_devices_panel", False),
            "advanced_control_enabled": data.get("advanced_control_enabled", False),
            "heating_curve_enabled": data.get("heating_curve_enabled", False),
            "pwm_enabled": data.get("pwm_enabled", False),
            "overshoot_protection_enabled": data.get("overshoot_protection_enabled", False),
            "default_heating_curve_coefficient": data.get("default_heating_curve_coefficient", 1.0),
            "default_min_consumption": data.get("default_min_consumption", 0.0),
            "default_max_consumption": data.get("default_max_consumption", 0.0),
            "default_boiler_capacity": data.get("default_boiler_capacity", 0.0),
            "default_opv": data.get("default_opv"),
            "global_presence_sensors": data.get("global_presence_sensors", []),
        }

    def build_save_data(
        self,
        global_config: dict[str, Any],
        area_service_data: list[dict],
        safety_service_data: dict[str, Any],
        preset_service_data: dict[str, float],
    ) -> dict[str, Any]:
        """Build the complete configuration dictionary for saving.

        Args:
            global_config: Global configuration values
            area_service_data: Area service data
            safety_service_data: Safety service data
            preset_service_data: Preset service data

        Returns:
            Complete configuration dictionary
        """
        data = {
            "opentherm_gateway_id": global_config.get("opentherm_gateway_id"),
            "trv_heating_temp": global_config.get("trv_heating_temp"),
            "trv_idle_temp": global_config.get("trv_idle_temp"),
            "trv_temp_offset": global_config.get("trv_temp_offset"),
            "frost_protection_enabled": global_config.get("frost_protection_enabled"),
            "frost_protection_temp": global_config.get("frost_protection_temp"),
            "hysteresis": global_config.get("hysteresis"),
            "hide_devices_panel": global_config.get("hide_devices_panel"),
            "global_presence_sensors": global_config.get("global_presence_sensors"),
            "advanced_control_enabled": global_config.get("advanced_control_enabled"),
            "heating_curve_enabled": global_config.get("heating_curve_enabled"),
            "pwm_enabled": global_config.get("pwm_enabled"),
            "overshoot_protection_enabled": global_config.get("overshoot_protection_enabled"),
            "default_heating_curve_coefficient": global_config.get(
                "default_heating_curve_coefficient"
            ),
            "default_min_consumption": global_config.get("default_min_consumption"),
            "default_max_consumption": global_config.get("default_max_consumption"),
            "default_boiler_capacity": global_config.get("default_boiler_capacity"),
            "default_opv": global_config.get("default_opv"),
            "areas": area_service_data,
            **safety_service_data,
            **preset_service_data,
        }
        return data
