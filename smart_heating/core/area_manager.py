"""Zone Manager for Smart Heating integration."""

import logging
from typing import Any, Dict, Deque, List
from collections import deque
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..models import DeviceEvent

from ..const import (
    DEFAULT_ACTIVITY_TEMP,
    DEFAULT_AWAY_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_FROST_PROTECTION_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_SLEEP_TEMP,
    DEFAULT_TRV_HEATING_TEMP,
    DEFAULT_TRV_IDLE_TEMP,
    DEFAULT_TRV_TEMP_OFFSET,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from ..models import Area, Schedule

_LOGGER = logging.getLogger(__name__)


class AreaManager:
    """Manage heating areas."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the area manager.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self.areas: dict[str, Area] = {}
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

        # Global OpenTherm gateway configuration
        self.opentherm_gateway_id: str | None = None  # Gateway device ID for service calls

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

        # Device event logging (in-memory per-area circular buffer)
        # Use a modest default capacity to avoid unbounded memory growth
        self._device_log_capacity: int = 500
        self._device_logs: dict[str, Deque[DeviceEvent]] = {}
        # Time-based retention for device events (minutes). Events older than this
        # will be purged from the per-area buffer. Default 60 minutes.
        self._device_event_retention_minutes: int = 60
        # Device log listeners (callbacks notified on new events)
        # Each listener is a callable accepting a single event dict parameter
        self._device_log_listeners: list = []

        # Advanced control features (disabled by default)
        self.advanced_control_enabled: bool = False
        self.heating_curve_enabled: bool = False
        self.pwm_enabled: bool = False
        self.pid_enabled: bool = False
        self.overshoot_protection_enabled: bool = False
        # Default heating curve coefficient (can be overridden per area)
        self.default_heating_curve_coefficient: float = 1.0

        # Global Preset Temperatures
        self.global_away_temp: float = DEFAULT_AWAY_TEMP
        self.global_eco_temp: float = DEFAULT_ECO_TEMP
        self.global_comfort_temp: float = DEFAULT_COMFORT_TEMP
        self.global_home_temp: float = DEFAULT_HOME_TEMP
        self.global_sleep_temp: float = DEFAULT_SLEEP_TEMP
        self.global_activity_temp: float = DEFAULT_ACTIVITY_TEMP

        # Optional consumption/power defaults used for derived sensors
        self.default_min_consumption: float = 0.0  # m³/h
        self.default_max_consumption: float = 0.0  # m³/h
        self.default_boiler_capacity: float = 0.0  # kW (if known)
        # Default overshoot protection value (OPV) in °C
        self.default_opv: float | None = None

        # Global Presence Sensors
        self.global_presence_sensors: list[dict] = []

        # Safety Sensors (smoke/CO detectors) - Multi-sensor support
        self.safety_sensors: list[dict] = []  # List of safety sensor configurations
        self.safety_sensor_id: str | None = None
        self.safety_sensor_attribute: str = "smoke"  # or "carbon_monoxide", "gas"
        self.safety_sensor_alert_value: str | bool = True  # Value that indicates danger
        self.safety_sensor_enabled: bool = True  # Enabled by default
        self._safety_alert_active: bool = False  # Current alert state
        self._safety_state_unsub = None  # State listener unsubscribe callback

        _LOGGER.debug("AreaManager initialized")

    async def async_load(self) -> None:
        """Load areas from storage."""
        _LOGGER.debug("Loading areas from storage")
        data = await self._store.async_load()

        if data is not None:
            # Load global configuration
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
            self.default_heating_curve_coefficient = data.get(
                "default_heating_curve_coefficient", 1.0
            )

            # Load global preset temperatures
            self.global_away_temp = data.get("global_away_temp", DEFAULT_AWAY_TEMP)
            self.global_eco_temp = data.get("global_eco_temp", DEFAULT_ECO_TEMP)
            self.global_comfort_temp = data.get("global_comfort_temp", DEFAULT_COMFORT_TEMP)
            self.global_home_temp = data.get("global_home_temp", DEFAULT_HOME_TEMP)
            self.global_sleep_temp = data.get("global_sleep_temp", DEFAULT_SLEEP_TEMP)
            self.global_activity_temp = data.get("global_activity_temp", DEFAULT_ACTIVITY_TEMP)
            self.default_min_consumption = data.get("default_min_consumption", 0.0)
            self.default_max_consumption = data.get("default_max_consumption", 0.0)
            self.default_boiler_capacity = data.get("default_boiler_capacity", 0.0)
            self.default_opv = data.get("default_opv")

            # Load global presence sensors
            self.global_presence_sensors = data.get("global_presence_sensors", [])

            # Load safety sensor configuration
            if "safety_sensors" in data:
                self.safety_sensors = data.get("safety_sensors", [])
            elif data.get("safety_sensor_id"):
                # Migrate old single sensor format to new list format
                _LOGGER.info("Migrating old safety sensor format to new multi-sensor format")
                self.safety_sensors = [
                    {
                        "sensor_id": data.get("safety_sensor_id"),
                        "attribute": data.get("safety_sensor_attribute", "smoke"),
                        "alert_value": data.get("safety_sensor_alert_value", True),
                        "enabled": data.get("safety_sensor_enabled", True),
                    }
                ]
            else:
                self.safety_sensors = []
            self._safety_alert_active = data.get("safety_alert_active", False)

            # Load areas
            if "areas" in data:
                for area_data in data["areas"]:
                    area = Area.from_dict(area_data)
                    area.area_manager = self  # Store reference to area_manager
                    self.areas[area.area_id] = area
                _LOGGER.info("Loaded %d areas from storage", len(self.areas))
        else:
            _LOGGER.debug("No areas found in storage")

    async def async_save(self) -> None:
        """Save areas to storage."""
        _LOGGER.debug("Saving areas to storage")
        data = {
            "opentherm_gateway_id": self.opentherm_gateway_id,
            # opentherm_enabled removed: whether control is active is determined by gateway existence
            "trv_heating_temp": self.trv_heating_temp,
            "trv_idle_temp": self.trv_idle_temp,
            "trv_temp_offset": self.trv_temp_offset,
            "frost_protection_enabled": self.frost_protection_enabled,
            "frost_protection_temp": self.frost_protection_temp,
            "hysteresis": self.hysteresis,
            "hide_devices_panel": self.hide_devices_panel,
            "global_away_temp": self.global_away_temp,
            "global_eco_temp": self.global_eco_temp,
            "global_comfort_temp": self.global_comfort_temp,
            "global_home_temp": self.global_home_temp,
            "global_sleep_temp": self.global_sleep_temp,
            "global_activity_temp": self.global_activity_temp,
            "global_presence_sensors": self.global_presence_sensors,
            "safety_sensors": self.safety_sensors,
            "safety_alert_active": self._safety_alert_active,
            "advanced_control_enabled": self.advanced_control_enabled,
            "heating_curve_enabled": self.heating_curve_enabled,
            "pwm_enabled": self.pwm_enabled,
            "pid_enabled": self.pid_enabled,
            "overshoot_protection_enabled": self.overshoot_protection_enabled,
            "default_heating_curve_coefficient": self.default_heating_curve_coefficient,
            "areas": [area.to_dict() for area in self.areas.values()],
            "default_min_consumption": self.default_min_consumption,
            "default_max_consumption": self.default_max_consumption,
            "default_boiler_capacity": self.default_boiler_capacity,
            "default_opv": self.default_opv,
        }
        await self._store.async_save(data)
        _LOGGER.info("Saved %d areas and global config to storage", len(self.areas))
