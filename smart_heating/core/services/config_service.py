"""Global configuration service."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from ...const import (
    DEFAULT_FROST_PROTECTION_TEMP,
    DEFAULT_TRV_HEATING_TEMP,
    DEFAULT_TRV_IDLE_TEMP,
    DEFAULT_TRV_TEMP_OFFSET,
)

_LOGGER = logging.getLogger(__name__)


class ConfigService:
    """Handles global configuration for the smart heating system."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize config service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

        # Global OpenTherm gateway configuration
        self.opentherm_gateway_id: str | None = None

        # Global TRV configuration
        self.trv_heating_temp: float = DEFAULT_TRV_HEATING_TEMP
        self.trv_idle_temp: float = DEFAULT_TRV_IDLE_TEMP
        self.trv_temp_offset: float = DEFAULT_TRV_TEMP_OFFSET

        # Global Frost Protection
        self.frost_protection_enabled: bool = False
        self.frost_protection_temp: float = DEFAULT_FROST_PROTECTION_TEMP

        # Global Hysteresis
        self.hysteresis: float = 0.5

        # UI Settings
        self.hide_devices_panel: bool = False

        # Advanced control features (disabled by default)
        self.advanced_control_enabled: bool = False
        self.heating_curve_enabled: bool = False
        self.pwm_enabled: bool = False
        self.pid_enabled: bool = False
        self.overshoot_protection_enabled: bool = False

        # Default heating curve coefficient (can be overridden per area)
        self.default_heating_curve_coefficient: float = 1.0

        # Optional consumption/power defaults used for derived sensors
        self.default_min_consumption: float = 0.0  # m³/h
        self.default_max_consumption: float = 0.0  # m³/h
        self.default_boiler_capacity: float = 0.0  # kW (if known)

        # Default overshoot protection value (OPV) in °C
        self.default_opv: float | None = None

        # Global Presence Sensors
        self.global_presence_sensors: list[dict] = []

    def load_config(self, data: dict[str, Any]) -> None:
        """Load global configuration from data.

        Args:
            data: Configuration dictionary
        """
        self.opentherm_gateway_id = data.get("opentherm_gateway_id")
        self.trv_heating_temp = data.get("trv_heating_temp", DEFAULT_TRV_HEATING_TEMP)
        self.trv_idle_temp = data.get("trv_idle_temp", DEFAULT_TRV_IDLE_TEMP)
        self.trv_temp_offset = data.get("trv_temp_offset", DEFAULT_TRV_TEMP_OFFSET)
        self.frost_protection_enabled = data.get("frost_protection_enabled", False)
        self.frost_protection_temp = data.get(
            "frost_protection_temp", DEFAULT_FROST_PROTECTION_TEMP
        )
        self.hysteresis = data.get("hysteresis", 0.5)
        self.hide_devices_panel = data.get("hide_devices_panel", False)
        self.advanced_control_enabled = data.get("advanced_control_enabled", False)
        self.heating_curve_enabled = data.get("heating_curve_enabled", False)
        self.pwm_enabled = data.get("pwm_enabled", False)
        self.pid_enabled = data.get("pid_enabled", False)
        self.overshoot_protection_enabled = data.get("overshoot_protection_enabled", False)
        self.default_heating_curve_coefficient = data.get("default_heating_curve_coefficient", 1.0)
        self.default_min_consumption = data.get("default_min_consumption", 0.0)
        self.default_max_consumption = data.get("default_max_consumption", 0.0)
        self.default_boiler_capacity = data.get("default_boiler_capacity", 0.0)
        self.default_opv = data.get("default_opv")
        self.global_presence_sensors = data.get("global_presence_sensors", [])

        _LOGGER.debug("Loaded global configuration")

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "opentherm_gateway_id": self.opentherm_gateway_id,
            "trv_heating_temp": self.trv_heating_temp,
            "trv_idle_temp": self.trv_idle_temp,
            "trv_temp_offset": self.trv_temp_offset,
            "frost_protection_enabled": self.frost_protection_enabled,
            "frost_protection_temp": self.frost_protection_temp,
            "hysteresis": self.hysteresis,
            "hide_devices_panel": self.hide_devices_panel,
            "global_presence_sensors": self.global_presence_sensors,
            "advanced_control_enabled": self.advanced_control_enabled,
            "heating_curve_enabled": self.heating_curve_enabled,
            "pwm_enabled": self.pwm_enabled,
            "pid_enabled": self.pid_enabled,
            "overshoot_protection_enabled": self.overshoot_protection_enabled,
            "default_heating_curve_coefficient": self.default_heating_curve_coefficient,
            "default_min_consumption": self.default_min_consumption,
            "default_max_consumption": self.default_max_consumption,
            "default_boiler_capacity": self.default_boiler_capacity,
            "default_opv": self.default_opv,
        }

    async def set_opentherm_gateway(self, gateway_id: str | None) -> None:
        """Set the global OpenTherm gateway device ID.

        Args:
            gateway_id: Device ID of the OpenTherm gateway
        """
        self.opentherm_gateway_id = gateway_id

        # Auto-enable heating curve when OpenTherm gateway is configured
        if gateway_id:
            if not self.advanced_control_enabled:
                self.advanced_control_enabled = True
                _LOGGER.info("Auto-enabled advanced control (OpenTherm gateway configured)")
            if not self.heating_curve_enabled:
                self.heating_curve_enabled = True
                _LOGGER.info("Auto-enabled heating curve for optimal energy efficiency")

        _LOGGER.info("OpenTherm gateway set to %s", gateway_id)

    def set_trv_temperatures(
        self, heating_temp: float, idle_temp: float, temp_offset: float | None = None
    ) -> None:
        """Set global TRV temperature limits.

        Args:
            heating_temp: Temperature to set when heating
            idle_temp: Temperature to set when idle
            temp_offset: Temperature offset above target
        """
        self.trv_heating_temp = heating_temp
        self.trv_idle_temp = idle_temp
        if temp_offset is not None:
            self.trv_temp_offset = temp_offset
            _LOGGER.info(
                "TRV temperatures set: heating=%.1f°C, idle=%.1f°C, offset=%.1f°C",
                heating_temp,
                idle_temp,
                temp_offset,
            )
        else:
            _LOGGER.info(
                "TRV temperatures set: heating=%.1f°C, idle=%.1f°C",
                heating_temp,
                idle_temp,
            )
