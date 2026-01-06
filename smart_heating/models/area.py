"""Area model for Smart Heating integration."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..const import (
    ATTR_AREA_ID,
    ATTR_AREA_NAME,
    ATTR_DEVICES,
    ATTR_ENABLED,
    ATTR_TARGET_TEMPERATURE,
    DEFAULT_ACTIVITY_TEMP,
    DEFAULT_AWAY_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_PRESENCE_TEMP_BOOST,
    DEFAULT_SLEEP_TEMP,
    DEFAULT_WINDOW_OPEN_TEMP_DROP,
    HVAC_MODE_HEAT,
    PRESET_AWAY,
    PRESET_HOME,
    PRESET_NONE,
    STATE_HEATING,
    STATE_IDLE,
    STATE_OFF,
)
from .area_boost_manager import AreaBoostManager
from .area_device_manager import AreaDeviceManager
from .area_preset_manager import AreaPresetManager
from .area_schedule_manager import AreaScheduleManager
from .area_sensor_manager import AreaSensorManager
from .schedule import Schedule

if TYPE_CHECKING:
    from ..core.area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


class Area:
    """Representation of a heating area."""

    def __init__(
        self,
        area_id: str,
        name: str,
        target_temperature: float = 20.0,
        enabled: bool = True,
    ) -> None:
        """Initialize a area.

        Args:
            area_id: Unique identifier for the area
            name: Display name of the area
            target_temperature: Target temperature for the area
            enabled: Whether the area is enabled
        """
        self.area_id = area_id
        self.name = name
        self.target_temperature = target_temperature
        self.enabled = enabled
        self.devices: dict[str, dict[str, Any]] = {}
        self.schedules: dict[str, Schedule] = {}
        self._current_temperature: float | None = None
        self.hidden: bool = False  # Whether area is hidden from main view
        self.area_manager: "AreaManager | None" = None  # Reference to parent AreaManager

        # Heating state tracking (runtime only, not persisted)
        # True = heating active, False = idle, None = initial/unknown
        self._last_heating_state: bool | None = None

        # Preset mode settings
        self.preset_mode: str = PRESET_NONE
        self.away_temp: float = DEFAULT_AWAY_TEMP
        self.eco_temp: float = DEFAULT_ECO_TEMP
        self.comfort_temp: float = DEFAULT_COMFORT_TEMP
        self.home_temp: float = DEFAULT_HOME_TEMP
        self.sleep_temp: float = DEFAULT_SLEEP_TEMP
        self.activity_temp: float = DEFAULT_ACTIVITY_TEMP

        # Preset configuration - choose between global or custom temperatures
        self.use_global_away: bool = True
        self.use_global_eco: bool = True
        self.use_global_comfort: bool = True
        self.use_global_home: bool = True
        self.use_global_sleep: bool = True
        self.use_global_activity: bool = True

        # HVAC mode (heat/cool/auto)
        self.hvac_mode: str = HVAC_MODE_HEAT

        # Window sensor settings (new config structure)
        self.window_sensors: list[dict[str, Any]] = []  # List of window sensor configs
        self.window_is_open: bool = False  # Cached state

        # Presence sensor settings (new config structure)
        self.presence_sensors: list[dict[str, Any]] = []  # List of presence sensor configs
        self.presence_detected: bool = False  # Cached state
        self.use_global_presence: bool = (
            False  # Use global presence sensors instead of area-specific
        )

        # Auto preset mode based on presence
        self.auto_preset_enabled: bool = False  # Automatically switch preset based on presence
        self.auto_preset_home: str = PRESET_HOME  # Preset when presence detected
        self.auto_preset_away: str = PRESET_AWAY  # Preset when no presence

        # Manual override mode - when user manually adjusts thermostat outside the app
        self.manual_override: bool = False  # True when thermostat was manually adjusted

        # Switch/pump control setting
        self.shutdown_switches_when_idle: bool = (
            True  # Turn off switches/pumps when area not heating
        )

        # Hysteresis override - None means use global setting
        self.hysteresis_override: float | None = None  # Area-specific hysteresis in °C (0.0-2.0)

        # Primary temperature sensor - which device to use for temperature reading
        self.primary_temperature_sensor: str | None = (
            None  # Entity ID of primary temp sensor (can be thermostat or temp sensor)
        )

        # Heating system type - affects OpenTherm setpoint calculation
        # Options: "radiator", "floor_heating", "airco"
        # "airco" denotes an air conditioning system and should bypass
        # boiler / radiator / valve control logic.
        self.heating_type: str = "radiator"
        self.custom_overhead_temp: float | None = None  # Custom overhead (overrides defaults)
        # Area-specific heating curve coefficient (optional, if None use global default)
        self.heating_curve_coefficient: float | None = None

        # Area-specific PID control settings
        self.pid_enabled: bool = False  # Enable PID control for this area
        self.pid_automatic_gains: bool = True  # Use automatic gain calculation
        self.pid_active_modes: list[str] = ["schedule", "home", "comfort"]  # Modes where PID runs

        # Initialize manager instances for composition
        self.device_manager = AreaDeviceManager(self)
        self.sensor_manager = AreaSensorManager(self)
        self.preset_manager = AreaPresetManager(self)
        self.schedule_manager = AreaScheduleManager(self)
        self.boost_manager = AreaBoostManager(self)

        # TRV entity configuration for this area
        # Each entry is a dict: {"entity_id": str, "role": "position"|"open"|"both"|None, "name": Optional[str]}
        self.trv_entities: list[dict[str, Any]] = []

    # Device management methods - delegate to AreaDeviceManager
    def add_device(self, device_id: str, device_type: str, mqtt_topic: str | None = None) -> None:
        """Add a device to the area.

        Args:
            device_id: Unique identifier for the device
            device_type: Type of device (thermostat, temperature_sensor, etc.)
            mqtt_topic: MQTT topic for the device (optional)
        """
        return self.device_manager.add_device(device_id, device_type, mqtt_topic)

    def remove_device(self, device_id: str) -> None:
        """Remove a device from the area.

        Args:
            device_id: Unique identifier for the device
        """
        return self.device_manager.remove_device(device_id)

    def get_temperature_sensors(self) -> list[str]:
        """Get all temperature sensor device IDs in the area.

        Returns:
            List of temperature sensor device IDs
        """
        return self.device_manager.get_temperature_sensors()

    def get_thermostats(self) -> list[str]:
        """Get all thermostat device IDs in the area.

        Returns:
            List of thermostat device IDs
        """
        return self.device_manager.get_thermostats()

    def get_opentherm_gateways(self) -> list[str]:
        """Get all OpenTherm gateway device IDs in the area.

        Returns:
            List of OpenTherm gateway device IDs
        """
        return self.device_manager.get_opentherm_gateways()

    def get_switches(self) -> list[str]:
        """Get all switch device IDs in the area (pumps, relays, etc.).

        Returns:
            List of switch device IDs
        """
        return self.device_manager.get_switches()

    def get_valves(self) -> list[str]:
        """Get all valve device IDs in the area (TRVs, motorized valves).

        Returns:
            List of valve device IDs
        """
        return self.device_manager.get_valves()

    # Sensor management methods - delegate to AreaSensorManager
    def add_window_sensor(
        self,
        entity_id: str,
        action_when_open: str = "reduce_temperature",
        temp_drop: float | None = None,
    ) -> None:
        """Add a window/door sensor to the area.

        Args:
            entity_id: Entity ID of the window/door sensor
            action_when_open: Action to take when window opens (turn_off, reduce_temperature, none)
            temp_drop: Temperature drop when open (only for reduce_temperature action)
        """
        return self.sensor_manager.add_window_sensor(entity_id, action_when_open, temp_drop)

    def remove_window_sensor(self, entity_id: str) -> None:
        """Remove a window/door sensor from the area.

        Args:
            entity_id: Entity ID of the window/door sensor
        """
        return self.sensor_manager.remove_window_sensor(entity_id)

    def add_presence_sensor(
        self,
        entity_id: str,
    ) -> None:
        """Add a presence/motion sensor to the area.

        Presence sensors control preset mode switching:
        - When away: Switch to "away" preset
        - When home: Switch back to previous preset (typically "home")

        Args:
            entity_id: Entity ID of the presence sensor (person.* or binary_sensor.*)
        """
        return self.sensor_manager.add_presence_sensor(entity_id)

    def remove_presence_sensor(self, entity_id: str) -> None:
        """Remove a presence/motion sensor from the area.

        Args:
            entity_id: Entity ID of the presence sensor
        """
        return self.sensor_manager.remove_presence_sensor(entity_id)

    def add_trv_entity(
        self, entity_id: str, role: str | None = None, name: str | None = None
    ) -> None:
        """Add a TRV-related entity to the area configuration.

        Args:
            entity_id: Entity ID (sensor or binary_sensor)
            role: Optional role: "position", "open", or "both"
            name: Optional friendly name override
        """
        # If entity exists, update role/name; otherwise add as new
        for e in self.trv_entities:
            if e.get("entity_id") == entity_id:
                e["role"] = role
                e["name"] = name
                return

        self.trv_entities.append({"entity_id": entity_id, "role": role, "name": name})

    def remove_trv_entity(self, entity_id: str) -> None:
        """Remove a TRV entity from the area configuration.

        Args:
            entity_id: Entity ID to remove
        """
        self.trv_entities = [e for e in self.trv_entities if e.get("entity_id") != entity_id]

    # Preset management methods - delegate to AreaPresetManager
    def get_preset_temperature(self) -> float:
        """Get the target temperature for the current preset mode.

        Returns:
            Temperature for current preset mode
        """
        return self.preset_manager.get_preset_temperature()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode for the area.

        Args:
            preset_mode: Preset mode (away, eco, comfort, etc.)
        """
        return self.preset_manager.set_preset_mode(preset_mode)

    def set_boost_mode(self, duration: int, temp: float | None = None) -> None:
        """Activate boost mode for a specified duration.

        Args:
            duration: Duration in minutes
            temp: Optional boost temperature (defaults to self.boost_temp)
        """
        return self.boost_manager.activate_boost(duration, temp)

    def cancel_boost_mode(self) -> None:
        """Cancel active boost mode."""
        return self.boost_manager.cancel_boost()

    def check_boost_expiry(self) -> bool:
        """Check if boost mode has expired and cancel if needed.

        Returns:
            True if boost was cancelled, False otherwise
        """
        return self.boost_manager.check_boost_expiry()

    # Schedule management methods - delegate to AreaScheduleManager
    def add_schedule(self, schedule: Schedule) -> None:
        """Add a schedule to the area.

        Args:
            schedule: Schedule instance
        """
        return self.schedule_manager.add_schedule(schedule)

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule from the area.

        Args:
            schedule_id: Schedule identifier
        """
        return self.schedule_manager.remove_schedule(schedule_id)

    def get_active_schedule_temperature(self, current_time: datetime | None = None) -> float | None:
        """Get the temperature from the currently active schedule.

        Args:
            current_time: Current time (defaults to now)

        Returns:
            Temperature from active schedule or None
        """
        return self.schedule_manager.get_active_schedule_temperature(current_time)

    def get_effective_target_temperature(self, current_time: datetime | None = None) -> float:
        """Get the effective target temperature considering all factors.

        Priority order:
        1. Boost mode (if active)
        2. Proactive maintenance (if active)
        3. Window open (reduce temperature)
        4. Preset mode temperature
        5. Schedule temperature
        6. Base target temperature
        7. Night boost adjustment
        8. Presence boost (if detected)

        Args:
            current_time: Current time (defaults to now)

        Returns:
            Effective target temperature
        """
        return self.schedule_manager.get_effective_target_temperature(current_time)

    @property
    def current_temperature(self) -> float | None:
        """Get the current temperature of the area.

        Returns:
            Current temperature or None
        """
        return self._current_temperature

    @current_temperature.setter
    def current_temperature(self, value: float | None) -> None:
        """Set the current temperature of the area.

        Args:
            value: New temperature value
        """
        self._current_temperature = value

    @property
    def state(self) -> str:
        """Get the current state of the area.

        Returns:
            Current state (heating, idle, off)
        """
        if not self.enabled:
            return STATE_OFF

        # Check if any thermostat is actively heating
        # This will be updated by the climate controller
        if hasattr(self, "_state"):
            return self._state

        # Fallback to temperature-based state
        if (
            self._current_temperature is not None
            and self.target_temperature is not None
            and self._current_temperature < self.target_temperature - 0.5
        ):
            return STATE_HEATING

        return STATE_IDLE

    @state.setter
    def state(self, value: str) -> None:
        """Set the current state of the area.

        Args:
            value: New state value
        """
        self._state = value

    def to_dict(self) -> dict[str, Any]:
        """Convert area to dictionary for storage.

        Returns:
            Dictionary representation of the area
        """
        return {
            ATTR_AREA_ID: self.area_id,
            ATTR_AREA_NAME: self.name,
            ATTR_TARGET_TEMPERATURE: self.target_temperature,
            ATTR_ENABLED: self.enabled,
            "hidden": self.hidden,
            "manual_override": self.manual_override,
            "shutdown_switches_when_idle": self.shutdown_switches_when_idle,
            ATTR_DEVICES: self.devices,
            "schedules": [s.to_dict() for s in self.schedules.values()],
            # Preset modes
            "preset_mode": self.preset_mode,
            "away_temp": self.away_temp,
            "eco_temp": self.eco_temp,
            "comfort_temp": self.comfort_temp,
            "home_temp": self.home_temp,
            "sleep_temp": self.sleep_temp,
            "activity_temp": self.activity_temp,
            # Global preset flags
            "use_global_away": self.use_global_away,
            "use_global_eco": self.use_global_eco,
            "use_global_comfort": self.use_global_comfort,
            "use_global_home": self.use_global_home,
            "use_global_sleep": self.use_global_sleep,
            "use_global_activity": self.use_global_activity,
            # Boost mode - delegate to boost_manager
            **self.boost_manager.to_dict(),
            # HVAC mode
            "hvac_mode": self.hvac_mode,
            # Window sensors (new structure)
            "window_sensors": self.window_sensors,
            # Presence sensors (new structure)
            "presence_sensors": self.presence_sensors,
            "use_global_presence": self.use_global_presence,
            # Auto preset mode
            "auto_preset_enabled": self.auto_preset_enabled,
            "auto_preset_home": self.auto_preset_home,
            "auto_preset_away": self.auto_preset_away,
            # Hysteresis override
            "hysteresis_override": self.hysteresis_override,
            # Primary temperature sensor
            "primary_temperature_sensor": self.primary_temperature_sensor,
            # Heating type configuration
            "heating_type": self.heating_type,
            "custom_overhead_temp": self.custom_overhead_temp,
            # Heating curve coefficient (area-specific override)
            "heating_curve_coefficient": self.heating_curve_coefficient,
            # PID control settings (area-specific)
            "pid_enabled": self.pid_enabled,
            "pid_automatic_gains": self.pid_automatic_gains,
            "pid_active_modes": self.pid_active_modes,
            # TRV entities configured for this area
            "trv_entities": self.trv_entities,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Area":
        """Create a area from dictionary.

        Args:
            data: Dictionary with area data

        Returns:
            Zone instance
        """
        area = cls(
            area_id=data[ATTR_AREA_ID],
            # Accept both 'area_name' and 'name' keys for compatibility with tests
            name=data.get(ATTR_AREA_NAME, data.get("name")),
            target_temperature=data.get(ATTR_TARGET_TEMPERATURE, 20.0),
            enabled=data.get(ATTR_ENABLED, True),
        )
        area.devices = data.get(ATTR_DEVICES, {})
        area.hidden = data.get("hidden", False)
        area.manual_override = data.get("manual_override", False)
        # Load shutdown setting; legacy key `switch_shutdown_enabled` has been removed
        # from persisted format and is no longer read. Use explicit `shutdown_switches_when_idle`.
        area.shutdown_switches_when_idle = data.get("shutdown_switches_when_idle", True)

        # Boost settings - delegate to boost_manager
        area.boost_manager = AreaBoostManager.from_dict(data, area)

        # Preset modes
        area.preset_mode = data.get("preset_mode", PRESET_NONE)
        area.away_temp = data.get("away_temp", DEFAULT_AWAY_TEMP)
        area.eco_temp = data.get("eco_temp", DEFAULT_ECO_TEMP)
        area.comfort_temp = data.get("comfort_temp", DEFAULT_COMFORT_TEMP)
        area.home_temp = data.get("home_temp", DEFAULT_HOME_TEMP)
        area.sleep_temp = data.get("sleep_temp", DEFAULT_SLEEP_TEMP)
        area.activity_temp = data.get("activity_temp", DEFAULT_ACTIVITY_TEMP)

        area.use_global_away = data.get("use_global_away", True)
        area.use_global_eco = data.get("use_global_eco", True)
        area.use_global_comfort = data.get("use_global_comfort", True)
        area.use_global_home = data.get("use_global_home", True)
        area.use_global_sleep = data.get("use_global_sleep", True)
        area.use_global_activity = data.get("use_global_activity", True)

        # HVAC mode
        area.hvac_mode = data.get("hvac_mode", HVAC_MODE_HEAT)

        # Hysteresis override
        area.hysteresis_override = data.get("hysteresis_override")

        # Primary temperature sensor
        area.primary_temperature_sensor = data.get("primary_temperature_sensor")

        # Heating type configuration
        area.heating_type = data.get("heating_type", "radiator")
        area.custom_overhead_temp = data.get("custom_overhead_temp")

        # Heating curve coefficient (area-specific override)
        area.heating_curve_coefficient = data.get("heating_curve_coefficient")

        # PID control settings (area-specific)
        area.pid_enabled = data.get("pid_enabled", False)
        area.pid_automatic_gains = data.get("pid_automatic_gains", True)
        area.pid_active_modes = data.get("pid_active_modes", ["schedule", "home", "comfort"])

        # TRV entities configuration (backwards compatible - default to empty list)
        area.trv_entities = data.get("trv_entities", [])

        # Window sensors - support both old string format and new dict format
        window_sensors_data = data.get("window_sensors", [])
        if window_sensors_data and isinstance(window_sensors_data[0], str):
            area.window_sensors = [
                {
                    "entity_id": entity_id,
                    "action_when_open": "reduce_temperature",
                    "temp_drop": data.get("window_open_temp_drop", DEFAULT_WINDOW_OPEN_TEMP_DROP),
                }
                for entity_id in window_sensors_data
            ]
        else:
            area.window_sensors = window_sensors_data

        # Presence sensors - support both old string format and new dict format
        presence_sensors_data = data.get("presence_sensors", [])
        if presence_sensors_data and isinstance(presence_sensors_data[0], str):
            area.presence_sensors = [
                {
                    "entity_id": entity_id,
                    "action_when_away": "reduce_temperature",
                    "action_when_home": "increase_temperature",
                    "temp_drop_when_away": 3.0,
                    "temp_boost_when_home": data.get(
                        "presence_temp_boost", DEFAULT_PRESENCE_TEMP_BOOST
                    ),
                }
                for entity_id in presence_sensors_data
            ]
        else:
            area.presence_sensors = presence_sensors_data

        # Global presence flag
        area.use_global_presence = data.get("use_global_presence", False)

        # Auto preset mode
        area.auto_preset_enabled = data.get("auto_preset_enabled", False)
        area.auto_preset_home = data.get("auto_preset_home", PRESET_HOME)
        area.auto_preset_away = data.get("auto_preset_away", PRESET_AWAY)

        # Load schedules
        for schedule_data in data.get("schedules", []):
            schedule = Schedule.from_dict(schedule_data)
            area.schedules[schedule.schedule_id] = schedule

        return area
