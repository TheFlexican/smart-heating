"""Device capability detection and caching.

This module provides capability discovery for heating/cooling devices,
detecting what features they support and determining optimal control parameters.
"""

from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)

# Home Assistant climate feature flags
SUPPORT_TARGET_TEMPERATURE = 1
SUPPORT_TARGET_TEMPERATURE_RANGE = 2
SUPPORT_TARGET_HUMIDITY = 4
SUPPORT_FAN_MODE = 8
SUPPORT_PRESET_MODE = 16
SUPPORT_SWING_MODE = 32
SUPPORT_AUX_HEAT = 64
SUPPORT_TURN_OFF = 128
SUPPORT_TURN_ON = 256


@dataclass
class DeviceCapabilities:
    """Device capability profile.

    Stores what a device can do and optimal control parameters.
    """

    # Core capabilities (detected from HA)
    supports_turn_off: bool
    supports_turn_on: bool
    supports_temperature: bool
    supports_position: bool
    supports_hvac_modes: list[str]

    # Temperature control
    min_temp: float
    max_temp: float
    temp_step: float

    # Optimal control parameters (learned or defaulted)
    optimal_off_temp: float | None  # What temp to set when "off" (0.0 for TRVs)
    optimal_idle_temp: float | None  # What temp to set when idle (10.0 for TRVs)
    heating_temp_offset: float  # Offset above target when heating (5.0 for TRVs)

    # Device metadata
    device_type: str  # "trv", "thermostat", "ac_unit", "valve"
    manufacturer: str | None = None
    model: str | None = None
    integration: str | None = None

    # Related entities
    power_switch: str | None = None
    valve_position: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "supports_turn_off": self.supports_turn_off,
            "supports_turn_on": self.supports_turn_on,
            "supports_temperature": self.supports_temperature,
            "supports_position": self.supports_position,
            "supports_hvac_modes": self.supports_hvac_modes,
            "min_temp": self.min_temp,
            "max_temp": self.max_temp,
            "temp_step": self.temp_step,
            "optimal_off_temp": self.optimal_off_temp,
            "optimal_idle_temp": self.optimal_idle_temp,
            "heating_temp_offset": self.heating_temp_offset,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "integration": self.integration,
            "power_switch": self.power_switch,
            "valve_position": self.valve_position,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceCapabilities":
        """Create from dictionary."""
        return cls(
            supports_turn_off=data.get("supports_turn_off", False),
            supports_turn_on=data.get("supports_turn_on", False),
            supports_temperature=data.get("supports_temperature", True),
            supports_position=data.get("supports_position", False),
            supports_hvac_modes=data.get("supports_hvac_modes", []),
            min_temp=data.get("min_temp", 5.0),
            max_temp=data.get("max_temp", 35.0),
            temp_step=data.get("temp_step", 0.5),
            optimal_off_temp=data.get("optimal_off_temp"),
            optimal_idle_temp=data.get("optimal_idle_temp"),
            heating_temp_offset=data.get("heating_temp_offset", 0.0),
            device_type=data.get("device_type", "thermostat"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            integration=data.get("integration"),
            power_switch=data.get("power_switch"),
            valve_position=data.get("valve_position"),
        )


@dataclass
class DeviceProfile:
    """Complete device profile with capabilities.

    Represents a discovered device with all its capabilities and metadata.
    """

    entity_id: str
    capabilities: DeviceCapabilities
    last_discovered: datetime
    discovery_method: str  # "ha_attributes", "mqtt_discovery", "manual"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "entity_id": self.entity_id,
            "capabilities": self.capabilities.to_dict(),
            "last_discovered": self.last_discovered.isoformat(),
            "discovery_method": self.discovery_method,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceProfile":
        """Create from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            capabilities=DeviceCapabilities.from_dict(data["capabilities"]),
            last_discovered=datetime.fromisoformat(data["last_discovered"]),
            discovery_method=data.get("discovery_method", "ha_attributes"),
        )


class DeviceCapabilityDetector:
    """Detect and cache device capabilities from Home Assistant.

    This class discovers what features devices support and determines
    optimal control parameters for each device type.
    """

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager):
        """Initialize device capability detector.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
        """
        self.hass = hass
        self.area_manager = area_manager
        self._profiles: dict[str, DeviceProfile] = {}

    async def discover_climate_device(self, entity_id: str) -> DeviceProfile:
        """Discover capabilities of a climate device.

        Args:
            entity_id: Climate entity ID to discover

        Returns:
            DeviceProfile with discovered capabilities

        Raises:
            ValueError: If entity not found
        """
        state = self.hass.states.get(entity_id)
        if not state:
            raise ValueError(f"Entity {entity_id} not found")

        # 1. Check HA supported_features
        features = state.attributes.get("supported_features", 0)
        supports_turn_off = bool(features & SUPPORT_TURN_OFF)
        supports_turn_on = bool(features & SUPPORT_TURN_ON)
        supports_target_temp = bool(features & SUPPORT_TARGET_TEMPERATURE)

        # 2. Get HVAC modes
        hvac_modes = state.attributes.get("hvac_modes", [])

        # 3. Get device info
        integration = entity_id.split(".")[0]
        device_info = self._get_device_info(entity_id)

        # 4. Determine device type
        device_type = self._detect_device_type(entity_id, state, integration)

        # 5. Get temperature range
        min_temp = state.attributes.get("min_temp", 5.0)
        max_temp = state.attributes.get("max_temp", 35.0)
        temp_step = state.attributes.get("target_temp_step", 0.5)

        # 6. Get related entities (power switch, valve position, etc.)
        related = self._find_related_entities(entity_id)

        # 7. Set optimal control parameters based on device type
        optimal_params = self._get_optimal_parameters(device_type)

        # Ensure heating_offset is always a float
        heating_offset = optimal_params["heating_offset"]
        if heating_offset is None:
            heating_offset = 0.0

        capabilities = DeviceCapabilities(
            supports_turn_off=supports_turn_off,
            supports_turn_on=supports_turn_on,
            supports_temperature=supports_target_temp,
            supports_position=False,  # TODO: Detect position support
            supports_hvac_modes=hvac_modes,
            min_temp=min_temp,
            max_temp=max_temp,
            temp_step=temp_step,
            optimal_off_temp=optimal_params["off_temp"],
            optimal_idle_temp=optimal_params["idle_temp"],
            heating_temp_offset=heating_offset,
            device_type=device_type,
            manufacturer=device_info.get("manufacturer"),
            model=device_info.get("model"),
            integration=integration,
            power_switch=related.get("power_switch"),
            valve_position=related.get("valve_position"),
        )

        profile = DeviceProfile(
            entity_id=entity_id,
            capabilities=capabilities,
            last_discovered=datetime.now(),
            discovery_method="ha_attributes",
        )

        _LOGGER.info(
            "Discovered device %s: type=%s, supports_turn_off=%s, off_temp=%s",
            entity_id,
            device_type,
            supports_turn_off,
            optimal_params["off_temp"],
        )

        return profile

    def _detect_device_type(self, entity_id: str, state: State, integration: str) -> str:
        """Detect device type from entity attributes.

        Args:
            entity_id: Entity ID
            state: Entity state
            integration: Integration domain

        Returns:
            Device type string
        """
        entity_lower = entity_id.lower()

        # Check for TRV indicators
        trv_patterns = [
            "radiatorknop",
            "radiator_knop",
            "trv",
            "radiator_valve",
            "thermostatic_valve",
            "valve",
        ]
        if any(pattern in entity_lower for pattern in trv_patterns):
            return "trv"

        # Check for AC indicators
        device_class = state.attributes.get("device_class")
        if device_class == "ac":
            return "ac_unit"

        hvac_modes = state.attributes.get("hvac_modes", [])
        if "cool" in hvac_modes or "heat_cool" in hvac_modes:
            return "ac_unit"

        # Check for valve with position control
        if integration == "mqtt" and "valve" in entity_lower:
            return "valve"

        # Default to regular thermostat
        return "thermostat"

    def _get_optimal_parameters(self, device_type: str) -> dict[str, float | None]:
        """Get optimal control parameters for device type.

        Args:
            device_type: Device type string

        Returns:
            Dictionary with optimal parameters (off_temp, idle_temp, heating_offset)
        """
        if device_type == "trv":
            return {
                "off_temp": 0.0,
                "idle_temp": 10.0,
                "heating_offset": 5.0,
            }
        elif device_type == "ac_unit":
            return {
                "off_temp": None,  # Use turn_off
                "idle_temp": None,
                "heating_offset": 0.0,
            }
        elif device_type == "valve":
            return {
                "off_temp": 0.0,
                "idle_temp": 5.0,
                "heating_offset": 0.0,
            }
        else:  # Regular thermostat
            frost_temp = (
                self.area_manager.frost_protection_temp
                if self.area_manager.frost_protection_enabled
                else 5.0
            )
            return {
                "off_temp": frost_temp,
                "idle_temp": None,  # Use hysteresis
                "heating_offset": 0.0,
            }

    def _get_device_info(self, entity_id: str) -> dict[str, str | None]:
        """Get device information from device registry.

        Args:
            entity_id: Entity ID

        Returns:
            Dictionary with manufacturer and model
        """
        entity_reg = er.async_get(self.hass)
        entity_entry = entity_reg.async_get(entity_id)

        if not entity_entry or not entity_entry.device_id:
            return {"manufacturer": None, "model": None}

        device_reg = dr.async_get(self.hass)
        device_entry = device_reg.async_get(entity_entry.device_id)

        if not device_entry:
            return {"manufacturer": None, "model": None}

        return {
            "manufacturer": device_entry.manufacturer,
            "model": device_entry.model,
        }

    def _find_related_entities(self, entity_id: str) -> dict[str, str | None]:
        """Find related entities (power switch, valve position, etc.).

        Args:
            entity_id: Base entity ID

        Returns:
            Dictionary with related entity IDs
        """
        related: dict[str, str | None] = {
            "power_switch": None,
            "valve_position": None,
        }

        # Extract base name from entity_id
        # climate.bedroom_trv -> bedroom_trv
        base_name = entity_id.split(".", 1)[1]

        # Look for power switch
        potential_switches = [
            f"switch.{base_name}_power",
            f"switch.{base_name}",
        ]
        for switch_id in potential_switches:
            if self.hass.states.get(switch_id):
                related["power_switch"] = switch_id
                break

        # Look for valve position
        potential_positions = [
            f"number.{base_name}_position",
            f"number.{base_name}_valve_position",
            f"sensor.{base_name}_position",
        ]
        for position_id in potential_positions:
            if self.hass.states.get(position_id):
                related["valve_position"] = position_id
                break

        return related

    def get_profile(self, entity_id: str) -> DeviceProfile | None:
        """Get cached device profile.

        Args:
            entity_id: Entity ID

        Returns:
            DeviceProfile if cached, None otherwise
        """
        return self._profiles.get(entity_id)

    async def discover_and_cache(self, entity_id: str) -> DeviceProfile:
        """Discover device and cache the profile.

        Args:
            entity_id: Entity ID to discover

        Returns:
            DeviceProfile
        """
        profile = await self.discover_climate_device(entity_id)
        self._profiles[entity_id] = profile
        return profile

    def load_profiles(self, profiles_data: dict[str, dict[str, Any]]) -> None:
        """Load device profiles from storage.

        Args:
            profiles_data: Dictionary of entity_id -> profile data
        """
        for entity_id, profile_data in profiles_data.items():
            try:
                profile = DeviceProfile.from_dict(profile_data)
                self._profiles[entity_id] = profile
                _LOGGER.debug("Loaded profile for %s", entity_id)
            except Exception as err:
                _LOGGER.debug("Failed to load profile for %s: %s", entity_id, err)

    def get_all_profiles(self) -> dict[str, dict[str, Any]]:
        """Get all profiles as dictionaries for storage.

        Returns:
            Dictionary of entity_id -> profile data
        """
        return {entity_id: profile.to_dict() for entity_id, profile in self._profiles.items()}

    async def rediscover_device(self, entity_id: str) -> DeviceProfile:
        """Force re-discovery of a device.

        Args:
            entity_id: Entity ID to rediscover

        Returns:
            Updated DeviceProfile
        """
        _LOGGER.info("Re-discovering device %s", entity_id)
        return await self.discover_and_cache(entity_id)
