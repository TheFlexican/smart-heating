"""State builder for coordinator updates."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from ...models import Area

_LOGGER = logging.getLogger(__name__)


class StateBuilder:
    """Builds area state data for coordinator updates.

    Extracts the logic from Coordinator._build_area_data (97 lines)
    into focused, testable methods.
    """

    def __init__(self, hass: HomeAssistant, coordinator) -> None:
        """Initialize state builder.

        Args:
            hass: Home Assistant instance
            coordinator: Coordinator instance (for helper methods)
        """
        self.hass = hass
        self.coordinator = coordinator

    def build_area_data(self, area_id: str, area: Area) -> dict[str, Any]:
        """Build comprehensive area state data.

        Replaces the 97-line _build_area_data method.

        Args:
            area_id: Area identifier
            area: Area instance

        Returns:
            Complete area state dictionary
        """
        return {
            **self._build_basic_info(area_id, area),
            **self._build_temperature_data(area),
            **self._build_device_states(area),
            **self._build_schedule_info(area),
            **self._build_preset_settings(area),
            **self._build_boost_mode(area),
            **self._build_sensor_config(area),
            **self._build_night_boost_config(area),
            **self._build_smart_boost_config(area),
            **self._build_control_state(area),
            **self._build_heating_config(area),
            **self._build_trv_states(area),
        }

    def _build_basic_info(self, area_id: str, area: Area) -> dict[str, Any]:
        """Build basic area information.

        Args:
            area_id: Area identifier
            area: Area instance

        Returns:
            Basic info dict
        """
        _LOGGER.debug(
            "Building data for area %s: manual_override=%s, target_temp=%s",
            area_id,
            getattr(area, "manual_override", False),
            area.target_temperature,
        )

        return {
            "id": area_id,  # Include area ID so frontend can identify and navigate
            "name": area.name,
            "enabled": area.enabled,
            "state": area.state,
            "device_count": len(area.devices),
            "hidden": getattr(area, "hidden", False),
            "manual_override": getattr(area, "manual_override", False),
        }

    def _build_temperature_data(self, area: Area) -> dict[str, Any]:
        """Build temperature-related data.

        Args:
            area: Area instance

        Returns:
            Temperature data dict
        """
        return {
            "target_temperature": area.target_temperature,
            "effective_target_temperature": area.get_effective_target_temperature(),
            "current_temperature": area.current_temperature,
        }

    def _build_device_states(self, area: Area) -> dict[str, Any]:
        """Build device state information.

        Args:
            area: Area instance

        Returns:
            Device states dict
        """
        devices_data = []
        for device_id, device_info in area.devices.items():
            device_data = self.coordinator._get_device_state_data(device_id, device_info)
            devices_data.append(device_data)

        return {"devices": devices_data}

    def _build_schedule_info(self, area: Area) -> dict[str, Any]:
        """Build schedule information.

        Args:
            area: Area instance

        Returns:
            Schedule info dict
        """
        schedules = [s.to_dict() for s in area.schedules.values()]

        return {"schedules": schedules}

    def _build_preset_settings(self, area: Area) -> dict[str, Any]:
        """Build preset mode settings.

        Args:
            area: Area instance

        Returns:
            Preset settings dict
        """
        return {
            "preset_mode": area.preset_mode,
            "away_temp": area.away_temp,
            "eco_temp": area.eco_temp,
            "comfort_temp": area.comfort_temp,
            "home_temp": area.home_temp,
            "sleep_temp": area.sleep_temp,
            "activity_temp": area.activity_temp,
            # Global preset flags
            "use_global_away": area.use_global_away,
            "use_global_eco": area.use_global_eco,
            "use_global_comfort": area.use_global_comfort,
            "use_global_home": area.use_global_home,
            "use_global_sleep": area.use_global_sleep,
            "use_global_activity": area.use_global_activity,
            # Global presence flag
            "use_global_presence": area.use_global_presence,
            # Auto preset mode
            "auto_preset_enabled": getattr(area, "auto_preset_enabled", False),
            "auto_preset_home": getattr(area, "auto_preset_home", "home"),
            "auto_preset_away": getattr(area, "auto_preset_away", "away"),
        }

    def _build_boost_mode(self, area: Area) -> dict[str, Any]:
        """Build boost mode settings.

        Args:
            area: Area instance

        Returns:
            Boost mode dict
        """
        return {
            "boost_mode_active": area.boost_manager.boost_mode_active,
            "boost_temp": area.boost_manager.boost_temp,
            "boost_duration": area.boost_manager.boost_duration,
        }

    def _build_sensor_config(self, area: Area) -> dict[str, Any]:
        """Build sensor configuration.

        Args:
            area: Area instance

        Returns:
            Sensor config dict
        """
        return {
            "window_sensors": area.window_sensors,
            "presence_sensors": area.presence_sensors,
            "primary_temperature_sensor": area.primary_temperature_sensor,
        }

    def _build_night_boost_config(self, area: Area) -> dict[str, Any]:
        """Build night boost configuration.

        Args:
            area: Area instance

        Returns:
            Night boost config dict
        """
        return {
            "night_boost_enabled": area.boost_manager.night_boost_enabled,
            "night_boost_offset": area.boost_manager.night_boost_offset,
            "night_boost_start_time": area.boost_manager.night_boost_start_time,
            "night_boost_end_time": area.boost_manager.night_boost_end_time,
        }

    def _build_smart_boost_config(self, area: Area) -> dict[str, Any]:
        """Build smart boost configuration.

        Args:
            area: Area instance

        Returns:
            Smart boost config dict
        """
        weather_data = self.coordinator._get_weather_state_data(
            area.boost_manager.weather_entity_id
        )

        return {
            "smart_boost_enabled": area.boost_manager.smart_boost_enabled,
            "smart_boost_target_time": area.boost_manager.smart_boost_target_time,
            "weather_entity_id": area.boost_manager.weather_entity_id,
            "weather_state": weather_data,
            # Proactive temperature maintenance
            "proactive_maintenance_enabled": area.boost_manager.proactive_maintenance_enabled,
            "proactive_maintenance_sensitivity": area.boost_manager.proactive_maintenance_sensitivity,
            "proactive_maintenance_min_trend": area.boost_manager.proactive_maintenance_min_trend,
            "proactive_maintenance_margin_minutes": area.boost_manager.proactive_maintenance_margin_minutes,
            "proactive_maintenance_cooldown_minutes": area.boost_manager.proactive_maintenance_cooldown_minutes,
        }

    def _build_control_state(self, area: Area) -> dict[str, Any]:
        """Build control state information.

        Args:
            area: Area instance

        Returns:
            Control state dict
        """
        return {
            "hvac_mode": area.hvac_mode,
            "hysteresis_override": area.hysteresis_override,
            "shutdown_switches_when_idle": getattr(area, "shutdown_switches_when_idle", True),
        }

    def _build_heating_config(self, area: Area) -> dict[str, Any]:
        """Build heating type configuration.

        Args:
            area: Area instance

        Returns:
            Heating config dict
        """
        return {
            "heating_type": getattr(area, "heating_type", "radiator"),
            "custom_overhead_temp": getattr(area, "custom_overhead_temp", None),
            "heating_curve_coefficient": getattr(area, "heating_curve_coefficient", None),
        }

    def _build_trv_states(self, area: Area) -> dict[str, Any]:
        """Build TRV states.

        Args:
            area: Area instance

        Returns:
            TRV states dict
        """
        trv_states = self.coordinator._get_trv_states_for_area(area)

        return {
            "trv_entities": getattr(area, "trv_entities", []),
            "trvs": trv_states,
        }
