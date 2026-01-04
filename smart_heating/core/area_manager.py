"""Area Manager facade for Smart Heating integration."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from ..models import Area, DeviceEvent, Schedule
from .services import (
    AreaService,
    ConfigService,
    DeviceService,
    PersistenceService,
    PresetService,
    SafetyService,
    ScheduleService,
)

_LOGGER = logging.getLogger(__name__)


class AreaManager:
    """Facade for managing heating areas and global configuration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the area manager facade.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._area_service = AreaService(hass)
        self._config_service = ConfigService(hass)
        self._device_service = DeviceService(hass)
        self._persistence_service = PersistenceService(hass)
        self._preset_service = PresetService(hass)
        self._safety_service = SafetyService(hass)
        self._schedule_service = ScheduleService(hass)

        _LOGGER.debug("AreaManager initialized")

    # ===== Area CRUD operations (delegate to AreaService) =====

    @property
    def areas(self) -> dict[str, Area]:
        """Get all areas.

        Returns:
            Dictionary of area_id -> Area
        """
        return self._area_service._areas

    def create_area(
        self,
        area_id: str,
        name: str,
        target_temperature: float = 20.0,
        enabled: bool = True,
        **kwargs: Any,
    ) -> Area:
        """Create a new area.

        Args:
            area_id: Unique identifier for the area
            name: Display name for the area
            target_temperature: Initial target temperature
            enabled: Whether area is enabled
            **kwargs: Additional area parameters

        Returns:
            Created Area instance

        Raises:
            ValueError: If area_id already exists
        """
        area = self._area_service.create_area(area_id, name, target_temperature, enabled, **kwargs)
        area.area_manager = self
        return area

    def add_area(self, area: Area) -> None:
        """Add an existing area.

        Args:
            area: Area instance to add

        Raises:
            ValueError: If area_id already exists
        """
        self._area_service.add_area(area)
        area.area_manager = self

    def delete_area(self, area_id: str) -> bool:
        """Delete an area.

        Args:
            area_id: Area identifier

        Returns:
            True if deleted, False if not found
        """
        return self._area_service.delete_area(area_id)

    def get_area(self, area_id: str) -> Area | None:
        """Get an area by ID.

        Args:
            area_id: Area identifier

        Returns:
            Area or None if not found
        """
        return self._area_service.get_area(area_id)

    def get_all_areas(self) -> dict[str, Area]:
        """Get all areas.

        Returns:
            Dictionary of all areas
        """
        return self._area_service.get_all_areas()

    def update_area_temperature(self, area_id: str, temperature: float) -> None:
        """Update the current temperature of an area.

        Args:
            area_id: Area identifier
            temperature: New temperature value

        Raises:
            ValueError: If area does not exist
        """
        self._area_service.update_area_temperature(area_id, temperature)

    def set_area_target_temperature(self, area_id: str, temperature: float) -> None:
        """Set the target temperature of an area.

        Args:
            area_id: Area identifier
            temperature: Target temperature

        Raises:
            ValueError: If area does not exist
        """
        self._area_service.set_area_target_temperature(area_id, temperature)

    def enable_area(self, area_id: str) -> None:
        """Enable an area.

        Args:
            area_id: Area identifier

        Raises:
            ValueError: If area does not exist
        """
        self._area_service.enable_area(area_id)

    def disable_area(self, area_id: str) -> None:
        """Disable an area.

        Args:
            area_id: Area identifier

        Raises:
            ValueError: If area does not exist
        """
        self._area_service.disable_area(area_id)

    # ===== Device operations (delegate to DeviceService) =====

    def add_device_to_area(
        self,
        area_id: str,
        device_id: str,
        device_type: str,
        mqtt_topic: str | None = None,
    ) -> None:
        """Add a device to an area.

        Args:
            area_id: Area identifier
            device_id: Device identifier
            device_type: Type of device
            mqtt_topic: MQTT topic for the device

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        self._device_service.add_device_to_area(area, device_id, device_type, mqtt_topic)

    def remove_device_from_area(self, area_id: str, device_id: str) -> None:
        """Remove a device from an area.

        Args:
            area_id: Area identifier
            device_id: Device identifier

        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        self._device_service.remove_device_from_area(area, device_id)

    def async_add_device_event(self, area_id: str, event: DeviceEvent) -> None:
        """Add a device event to the logs.

        Args:
            area_id: Area identifier
            event: Device event to log
        """
        self._device_service.async_add_device_event(area_id, event)

    def async_get_device_logs(
        self,
        area_id: str,
        device_id: str | None = None,
        direction: str | None = None,
        since: str | None = None,
    ) -> list[dict]:
        """Retrieve device logs with optional filtering.

        Args:
            area_id: Area identifier
            device_id: Optional device ID filter
            direction: Optional direction filter
            since: Optional ISO timestamp filter

        Returns:
            List of device event dicts
        """
        return self._device_service.async_get_device_logs(area_id, device_id, direction, since)

    def add_device_log_listener(self, cb) -> None:
        """Register a callback to receive device events.

        Args:
            cb: Callback function
        """
        self._device_service.add_device_log_listener(cb)

    def remove_device_log_listener(self, cb) -> None:
        """Remove a previously registered listener.

        Args:
            cb: Callback function
        """
        self._device_service.remove_device_log_listener(cb)

    # ===== Schedule operations (delegate to ScheduleService) =====

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
        return self._schedule_service.add_schedule_to_area(
            area, schedule_id, time, temperature, days
        )

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
        self._schedule_service.remove_schedule_from_area(area, schedule_id)

    # ===== Safety operations (delegate to SafetyService) =====

    def add_safety_sensor(
        self,
        sensor_id: str,
        attribute: str = "smoke",
        alert_value: str | bool = True,
        enabled: bool = True,
    ) -> None:
        """Add a safety sensor.

        Args:
            sensor_id: Entity ID of the safety sensor
            attribute: Attribute to monitor
            alert_value: Value that indicates danger
            enabled: Whether monitoring is enabled
        """
        self._safety_service.add_safety_sensor(sensor_id, attribute, alert_value, enabled)

    def remove_safety_sensor(self, sensor_id: str) -> None:
        """Remove a safety sensor.

        Args:
            sensor_id: Entity ID of the safety sensor
        """
        self._safety_service.remove_safety_sensor(sensor_id)

    def get_safety_sensors(self) -> list[dict[str, Any]]:
        """Get all configured safety sensors.

        Returns:
            List of safety sensor configurations
        """
        return self._safety_service.get_safety_sensors()

    def clear_safety_sensors(self) -> None:
        """Clear all configured safety sensors."""
        self._safety_service.clear_safety_sensors()

    def check_safety_sensor_status(self) -> tuple[bool, str | None]:
        """Check if any safety sensor is in alert state.

        Returns:
            Tuple of (is_alert, sensor_id)
        """
        return self._safety_service.check_safety_sensor_status()

    def is_safety_alert_active(self) -> bool:
        """Check if safety alert is currently active.

        Returns:
            True if in emergency shutdown mode
        """
        return self._safety_service.is_safety_alert_active()

    def set_safety_alert_active(self, active: bool) -> None:
        """Set the safety alert state.

        Args:
            active: Whether safety alert is active
        """
        self._safety_service.set_safety_alert_active(active)

    # ===== Global configuration properties (delegate to ConfigService) =====

    @property
    def opentherm_gateway_id(self) -> str | None:
        """Get OpenTherm gateway ID."""
        return self._config_service.opentherm_gateway_id

    @opentherm_gateway_id.setter
    def opentherm_gateway_id(self, value: str | None) -> None:
        """Set OpenTherm gateway ID."""
        self._config_service.opentherm_gateway_id = value

    @property
    def trv_heating_temp(self) -> float:
        """Get TRV heating temperature."""
        return self._config_service.trv_heating_temp

    @trv_heating_temp.setter
    def trv_heating_temp(self, value: float) -> None:
        """Set TRV heating temperature."""
        self._config_service.trv_heating_temp = value

    @property
    def trv_idle_temp(self) -> float:
        """Get TRV idle temperature."""
        return self._config_service.trv_idle_temp

    @trv_idle_temp.setter
    def trv_idle_temp(self, value: float) -> None:
        """Set TRV idle temperature."""
        self._config_service.trv_idle_temp = value

    @property
    def trv_temp_offset(self) -> float:
        """Get TRV temperature offset."""
        return self._config_service.trv_temp_offset

    @trv_temp_offset.setter
    def trv_temp_offset(self, value: float) -> None:
        """Set TRV temperature offset."""
        self._config_service.trv_temp_offset = value

    @property
    def frost_protection_enabled(self) -> bool:
        """Get frost protection enabled state."""
        return self._config_service.frost_protection_enabled

    @frost_protection_enabled.setter
    def frost_protection_enabled(self, value: bool) -> None:
        """Set frost protection enabled state."""
        self._config_service.frost_protection_enabled = value

    @property
    def frost_protection_temp(self) -> float:
        """Get frost protection temperature."""
        return self._config_service.frost_protection_temp

    @frost_protection_temp.setter
    def frost_protection_temp(self, value: float) -> None:
        """Set frost protection temperature."""
        self._config_service.frost_protection_temp = value

    @property
    def hysteresis(self) -> float:
        """Get hysteresis value."""
        return self._config_service.hysteresis

    @hysteresis.setter
    def hysteresis(self, value: float) -> None:
        """Set hysteresis value."""
        self._config_service.hysteresis = value

    @property
    def advanced_control_enabled(self) -> bool:
        """Get advanced control enabled state."""
        return self._config_service.advanced_control_enabled

    @advanced_control_enabled.setter
    def advanced_control_enabled(self, value: bool) -> None:
        """Set advanced control enabled state."""
        self._config_service.advanced_control_enabled = value

    @property
    def heating_curve_enabled(self) -> bool:
        """Get heating curve enabled state."""
        return self._config_service.heating_curve_enabled

    @heating_curve_enabled.setter
    def heating_curve_enabled(self, value: bool) -> None:
        """Set heating curve enabled state."""
        self._config_service.heating_curve_enabled = value

    @property
    def pwm_enabled(self) -> bool:
        """Get PWM enabled state."""
        return self._config_service.pwm_enabled

    @pwm_enabled.setter
    def pwm_enabled(self, value: bool) -> None:
        """Set PWM enabled state."""
        self._config_service.pwm_enabled = value

    @property
    def overshoot_protection_enabled(self) -> bool:
        """Get overshoot protection enabled state."""
        return self._config_service.overshoot_protection_enabled

    @overshoot_protection_enabled.setter
    def overshoot_protection_enabled(self, value: bool) -> None:
        """Set overshoot protection enabled state."""
        self._config_service.overshoot_protection_enabled = value

    @property
    def default_heating_curve_coefficient(self) -> float:
        """Get default heating curve coefficient."""
        return self._config_service.default_heating_curve_coefficient

    @default_heating_curve_coefficient.setter
    def default_heating_curve_coefficient(self, value: float) -> None:
        """Set default heating curve coefficient."""
        self._config_service.default_heating_curve_coefficient = value

    @property
    def default_min_consumption(self) -> float:
        """Get default minimum consumption."""
        return self._config_service.default_min_consumption

    @default_min_consumption.setter
    def default_min_consumption(self, value: float) -> None:
        """Set default minimum consumption."""
        self._config_service.default_min_consumption = value

    @property
    def default_max_consumption(self) -> float:
        """Get default maximum consumption."""
        return self._config_service.default_max_consumption

    @default_max_consumption.setter
    def default_max_consumption(self, value: float) -> None:
        """Set default maximum consumption."""
        self._config_service.default_max_consumption = value

    @property
    def default_boiler_capacity(self) -> float:
        """Get default boiler capacity."""
        return self._config_service.default_boiler_capacity

    @default_boiler_capacity.setter
    def default_boiler_capacity(self, value: float) -> None:
        """Set default boiler capacity."""
        self._config_service.default_boiler_capacity = value

    @property
    def default_opv(self) -> float | None:
        """Get default overshoot protection value."""
        return self._config_service.default_opv

    @default_opv.setter
    def default_opv(self, value: float | None) -> None:
        """Set default overshoot protection value."""
        self._config_service.default_opv = value

    @property
    def global_presence_sensors(self) -> list[dict]:
        """Get global presence sensors."""
        return self._config_service.global_presence_sensors

    @global_presence_sensors.setter
    def global_presence_sensors(self, value: list[dict]) -> None:
        """Set global presence sensors."""
        self._config_service.global_presence_sensors = value

    # ===== Preset temperature properties (delegate to PresetService) =====

    @property
    def global_away_temp(self) -> float:
        """Get global away temperature."""
        return self._preset_service.global_away_temp

    @global_away_temp.setter
    def global_away_temp(self, value: float) -> None:
        """Set global away temperature."""
        self._preset_service.global_away_temp = value

    @property
    def global_eco_temp(self) -> float:
        """Get global eco temperature."""
        return self._preset_service.global_eco_temp

    @global_eco_temp.setter
    def global_eco_temp(self, value: float) -> None:
        """Set global eco temperature."""
        self._preset_service.global_eco_temp = value

    @property
    def global_comfort_temp(self) -> float:
        """Get global comfort temperature."""
        return self._preset_service.global_comfort_temp

    @global_comfort_temp.setter
    def global_comfort_temp(self, value: float) -> None:
        """Set global comfort temperature."""
        self._preset_service.global_comfort_temp = value

    @property
    def global_home_temp(self) -> float:
        """Get global home temperature."""
        return self._preset_service.global_home_temp

    @global_home_temp.setter
    def global_home_temp(self, value: float) -> None:
        """Set global home temperature."""
        self._preset_service.global_home_temp = value

    @property
    def global_sleep_temp(self) -> float:
        """Get global sleep temperature."""
        return self._preset_service.global_sleep_temp

    @global_sleep_temp.setter
    def global_sleep_temp(self, value: float) -> None:
        """Set global sleep temperature."""
        self._preset_service.global_sleep_temp = value

    @property
    def global_activity_temp(self) -> float:
        """Get global activity temperature."""
        return self._preset_service.global_activity_temp

    @global_activity_temp.setter
    def global_activity_temp(self, value: float) -> None:
        """Set global activity temperature."""
        self._preset_service.global_activity_temp = value

    # ===== Configuration methods =====

    async def set_opentherm_gateway(self, gateway_id: str | None) -> None:
        """Set the global OpenTherm gateway device ID.

        Args:
            gateway_id: Device ID of the OpenTherm gateway
        """
        await self._config_service.set_opentherm_gateway(gateway_id)
        await self.async_save()

    def set_trv_temperatures(
        self, heating_temp: float, idle_temp: float, temp_offset: float | None = None
    ) -> None:
        """Set global TRV temperature limits.

        Args:
            heating_temp: Temperature to set when heating
            idle_temp: Temperature to set when idle
            temp_offset: Temperature offset above target
        """
        self._config_service.set_trv_temperatures(heating_temp, idle_temp, temp_offset)

    # ===== Persistence operations (delegate to PersistenceService) =====

    async def async_load(self) -> None:
        """Load areas and configuration from storage."""
        _LOGGER.debug("Loading areas from storage")
        data = await self._persistence_service.async_load()

        if data is not None:
            # Load global configuration
            global_config = self._persistence_service.load_global_config(data)
            self._config_service.load_config(global_config)

            # Load preset temperatures
            self._preset_service.load_presets(data)

            # Load safety sensor configuration
            self._safety_service.load_safety_config(data)

            # Load areas
            if "areas" in data:
                self._area_service.load_areas(data["areas"])
                # Set area_manager reference for all loaded areas
                for area in self._area_service.get_all_areas().values():
                    area.area_manager = self
                _LOGGER.info("Loaded %d areas from storage", len(self.areas))
        else:
            _LOGGER.debug("No areas found in storage")

    async def async_save(self) -> None:
        """Save areas and configuration to storage."""
        _LOGGER.debug("Saving areas to storage")
        data = self._persistence_service.build_save_data(
            self._config_service.to_dict(),
            self._area_service.to_dict(),
            self._safety_service.to_dict(),
            self._preset_service.to_dict(),
        )
        await self._persistence_service.async_save(data)
        _LOGGER.info("Saved %d areas and global config to storage", len(self.areas))
