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

    def get_area(self, area_id: str) -> Area | None:
        """Get a area by ID.

        Args:
            area_id: Zone identifier

        Returns:
            Zone or None if not found
        """
        return self.areas.get(area_id)

    def get_all_areas(self) -> dict[str, Area]:
        """Get all areas.

        Returns:
            Dictionary of all areas
        """
        return self.areas

    def find_area_by_device(self, device_id: str) -> str | None:
        """Find an area that contains the given device ID.

        Returns the `area_id` or None if not found.
        """
        for area_id, area in self.areas.items():
            if device_id in getattr(area, "devices", {}):
                return area_id
        return None

    def add_device_to_area(
        self,
        area_id: str,
        device_id: str,
        device_type: str,
        mqtt_topic: str | None = None,
    ) -> None:
        """Add a device to a area.

        Args:
            area_id: Zone identifier
            device_id: Device identifier
            device_type: Type of device
            mqtt_topic: MQTT topic for the device

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.add_device(device_id, device_type, mqtt_topic)

    def remove_device_from_area(self, area_id: str, device_id: str) -> None:
        """Remove a device from a area.

        Args:
            area_id: Zone identifier
            device_id: Device identifier

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.remove_device(device_id)

    def update_area_temperature(self, area_id: str, temperature: float) -> None:
        """Update the current temperature of a area.

        Args:
            area_id: Zone identifier
            temperature: New temperature value

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.current_temperature = temperature
        _LOGGER.debug("Updated area %s temperature to %.1f°C", area_id, temperature)

    def set_area_target_temperature(self, area_id: str, temperature: float) -> None:
        """Set the target temperature of a area.

        Args:
            area_id: Zone identifier
            temperature: Target temperature

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        old_temp = area.target_temperature
        area.target_temperature = temperature
        _LOGGER.info(
            "TARGET TEMP CHANGE for %s: %.1f°C → %.1f°C (preset: %s)",
            area_id,
            old_temp,
            temperature,
            area.preset_mode,
        )

    def enable_area(self, area_id: str) -> None:
        """Enable a area.

        Args:
            area_id: Zone identifier

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.enabled = True
        _LOGGER.info("Enabled area %s", area_id)

    def disable_area(self, area_id: str) -> None:
        """Disable a area.

        Args:
            area_id: Zone identifier

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.enabled = False
        _LOGGER.info("Disabled area %s", area_id)

    def add_schedule_to_area(
        self,
        area_id: str,
        schedule_id: str,
        time: str,
        temperature: float,
        days: list[str] | None = None,
    ) -> Schedule:
        """Add a schedule to an area.

        Args:
            area_id: Area identifier
            schedule_id: Unique schedule identifier
            time: Time in HH:MM format
            temperature: Target temperature
            days: Days of week or None for all days

        Returns:
            Created schedule

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        schedule = Schedule(schedule_id, time, temperature, days)
        area.add_schedule(schedule)
        _LOGGER.info("Added schedule %s to area %s", schedule_id, area_id)
        return schedule

    def remove_schedule_from_area(self, area_id: str, schedule_id: str) -> None:
        """Remove a schedule from an area.

        Args:
            area_id: Area identifier
            schedule_id: Schedule identifier

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        area.remove_schedule(schedule_id)
        _LOGGER.info("Removed schedule %s from area %s", schedule_id, area_id)

    async def set_opentherm_gateway(self, gateway_id: str | None) -> None:
        """Set the global OpenTherm gateway device ID.

        Args:
            gateway_id: Device ID of the OpenTherm gateway (from integration configuration ID field)
        """
        self.opentherm_gateway_id = gateway_id

        # Auto-enable heating curve when OpenTherm gateway is configured
        # This provides SAT-like optimal heating out of the box
        if gateway_id:
            if not self.advanced_control_enabled:
                self.advanced_control_enabled = True
                _LOGGER.info("Auto-enabled advanced control (OpenTherm gateway configured)")
            if not self.heating_curve_enabled:
                self.heating_curve_enabled = True
                _LOGGER.info("Auto-enabled heating curve for optimal energy efficiency")

        # When a gateway id is configured, the integration will control it automatically.
        _LOGGER.info("OpenTherm gateway set to %s", gateway_id)
        await self.async_save()

    def add_safety_sensor(
        self,
        sensor_id: str,
        attribute: str = "smoke",
        alert_value: str | bool = True,
        enabled: bool = True,
    ) -> None:
        """Add a safety sensor (smoke/CO detector).

        Args:
            sensor_id: Entity ID of the safety sensor
            attribute: Attribute to monitor (e.g., "smoke", "carbon_monoxide", "gas", "state")
            alert_value: Value that indicates danger (True, "on", "alarm", etc.)
            enabled: Whether safety monitoring is enabled for this sensor
        """
        # Check if sensor already exists
        for sensor in self.safety_sensors:
            if sensor["sensor_id"] == sensor_id:
                # Update existing sensor
                sensor["attribute"] = attribute
                sensor["alert_value"] = alert_value
                sensor["enabled"] = enabled
                _LOGGER.info(
                    "Safety sensor updated: %s (attribute: %s, alert_value: %s, enabled: %s)",
                    sensor_id,
                    attribute,
                    alert_value,
                    enabled,
                )
                return

        # Add new sensor
        self.safety_sensors.append(
            {
                "sensor_id": sensor_id,
                "attribute": attribute,
                "alert_value": alert_value,
                "enabled": enabled,
            }
        )
        _LOGGER.info(
            "Safety sensor added: %s (attribute: %s, alert_value: %s, enabled: %s)",
            sensor_id,
            attribute,
            alert_value,
            enabled,
        )

    def remove_safety_sensor(self, sensor_id: str) -> None:
        """Remove a safety sensor by ID.

        Args:
            sensor_id: Entity ID of the safety sensor to remove
        """
        self.safety_sensors = [s for s in self.safety_sensors if s["sensor_id"] != sensor_id]
        # Clear alert if no sensors remain
        if not self.safety_sensors:
            self._safety_alert_active = False
        _LOGGER.info("Safety sensor removed: %s", sensor_id)

    def get_safety_sensors(self) -> list[dict[str, Any]]:
        """Get all configured safety sensors.

        Returns:
            List of safety sensor configurations
        """
        return self.safety_sensors.copy()

    def clear_safety_sensors(self) -> None:
        """Clear all configured safety sensors."""
        self.safety_sensors = []
        self._safety_alert_active = False
        _LOGGER.info("Cleared all safety sensors")

    def check_safety_sensor_status(self) -> tuple[bool, str | None]:
        """Check if any safety sensor is in alert state.

        Returns:
            Tuple of (is_alert, sensor_id) - True if any sensor is alerting, with the sensor ID
        """
        if not self.safety_sensors:
            return False, None

        for sensor in self.safety_sensors:
            if not sensor.get("enabled", True):
                continue

            sensor_id = sensor["sensor_id"]
            attribute = sensor.get("attribute", "smoke")
            alert_value = sensor.get("alert_value", True)

            state = self.hass.states.get(sensor_id)
            if not state:
                _LOGGER.debug("Safety sensor %s not found", sensor_id)
                continue

            # Check the specified attribute or state
            if attribute == "state":
                # Check state directly
                current_value = state.state
            else:
                # Check attribute
                current_value = state.attributes.get(attribute)

            # Compare with alert value
            is_alert = current_value == alert_value

            if is_alert:
                _LOGGER.warning(
                    "\ud83d\udea8 Safety sensor %s is in alert state! %s = %s",
                    sensor_id,
                    attribute,
                    current_value,
                )
                return True, sensor_id

        # No sensors in alert state
        return False, None

    def is_safety_alert_active(self) -> bool:
        """Check if safety alert is currently active.

        Returns:
            True if in emergency shutdown mode due to safety alert
        """
        return self._safety_alert_active

    def set_safety_alert_active(self, active: bool) -> None:
        """Set the safety alert state.

        Args:
            active: Whether safety alert is active
        """
        if self._safety_alert_active != active:
            self._safety_alert_active = active
            _LOGGER.info("Safety alert state changed to: %s", active)

    def set_trv_temperatures(
        self, heating_temp: float, idle_temp: float, temp_offset: float | None = None
    ) -> None:
        """Set global TRV temperature limits for areas without position control.

        Args:
            heating_temp: Temperature to set when heating (default 25°C)
            idle_temp: Temperature to set when idle (default 10°C)
            temp_offset: Temperature offset above target for temp-controlled valves (default 10°C)
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

    def async_add_device_event(self, area_id: str, event: DeviceEvent) -> None:
        """Add a device event to the per-area in-memory log.

        This stores the event in a circular buffer and is intended for
        lightweight debugging and the Logs UI. Events are kept in memory
        only (no persistence) and the buffer size is limited by
        `self._device_log_capacity`.
        """
        logs = self._device_logs.get(area_id)
        if logs is None:
            logs = deque(maxlen=self._device_log_capacity)
            self._device_logs[area_id] = logs

        logs.append(event)

        # Purge events older than retention window (best-effort)
        try:
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(minutes=self._device_event_retention_minutes)
            # left-most entry is oldest (append -> right). Remove while too-old.
            while logs:
                oldest = logs[0]
                try:
                    oldest_ts = datetime.fromisoformat(oldest.timestamp.rstrip("Z"))
                except Exception:
                    break
                if oldest_ts < cutoff:
                    logs.popleft()
                else:
                    break
        except Exception:
            # Swallow any purge errors to avoid breaking event recording
            pass
        _LOGGER.debug("Recorded device event for area %s: %s", area_id, event.to_dict())

        # Notify listeners (best-effort, non-blocking)
        event_dict = event.to_dict()
        for listener in self._device_log_listeners:
            try:
                res = listener(event_dict)
                # If listener returned a coroutine, schedule it
                if hasattr(res, "__await__"):
                    try:
                        self.hass.async_create_task(res)
                    except Exception:
                        _LOGGER.debug("Failed to schedule listener coroutine for device event")
            except Exception:
                _LOGGER.exception("Device log listener raised an exception")

    def async_get_device_logs(
        self,
        area_id: str,
        limit: int = 100,
        since: str | None = None,
        device_id: str | None = None,
        direction: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve device logs for an area.

        Returns newest-first list of event dicts, filtered by optional
        `since` (ISO timestamp), `device_id`, and `direction` ("sent"/"received").
        """
        logs = self._device_logs.get(area_id, deque())
        results: List[Dict[str, Any]] = []

        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.rstrip("Z"))
            except Exception:
                since_dt = None

        for ev in reversed(logs):
            if len(results) >= limit:
                break

            if device_id and ev.device_id != device_id:
                continue
            if direction and ev.direction != direction:
                continue

            if since_dt:
                try:
                    ev_ts = datetime.fromisoformat(ev.timestamp.rstrip("Z"))
                    if ev_ts < since_dt:
                        continue
                except Exception:
                    # If parsing fails, include the event
                    pass

            results.append(ev.to_dict())

        return results

    def add_device_log_listener(self, callback) -> None:
        """Register a listener callable to receive new device events.

        The callback will be called with a single argument: the event dict.
        """
        if callback not in self._device_log_listeners:
            self._device_log_listeners.append(callback)

    def remove_device_log_listener(self, callback) -> None:
        """Remove a previously registered device log listener."""
        try:
            self._device_log_listeners.remove(callback)
        except ValueError:
            pass
