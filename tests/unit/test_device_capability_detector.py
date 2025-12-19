"""Tests for device capability detector."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import State
from smart_heating.features.device_capability_detector import (
    DeviceCapabilities,
    DeviceCapabilityDetector,
    DeviceProfile,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_area_manager():
    """Create a mock area manager."""
    manager = MagicMock()
    manager.frost_protection_enabled = True
    manager.frost_protection_temp = 5.0
    return manager


@pytest.fixture
def detector(mock_hass, mock_area_manager):
    """Create a detector instance."""
    return DeviceCapabilityDetector(mock_hass, mock_area_manager)


class TestDeviceCapabilities:
    """Test DeviceCapabilities dataclass."""

    def test_to_dict(self):
        """Test converting capabilities to dict."""
        caps = DeviceCapabilities(
            supports_turn_off=False,
            supports_turn_on=True,
            supports_temperature=True,
            supports_position=False,
            supports_hvac_modes=["heat", "off"],
            min_temp=5.0,
            max_temp=30.0,
            temp_step=0.5,
            optimal_off_temp=0.0,
            optimal_idle_temp=10.0,
            heating_temp_offset=5.0,
            device_type="trv",
            manufacturer="Danfoss",
            model="TRV-100",
            integration="mqtt",
            power_switch=None,
            valve_position="number.trv_position",
        )

        data = caps.to_dict()
        assert data["supports_turn_off"] is False
        assert data["device_type"] == "trv"
        assert data["optimal_off_temp"] == 0.0
        assert data["valve_position"] == "number.trv_position"

    def test_from_dict(self):
        """Test creating capabilities from dict."""
        data = {
            "supports_turn_off": False,
            "supports_turn_on": True,
            "supports_temperature": True,
            "supports_position": False,
            "supports_hvac_modes": ["heat"],
            "min_temp": 5.0,
            "max_temp": 30.0,
            "temp_step": 0.5,
            "optimal_off_temp": 0.0,
            "optimal_idle_temp": 10.0,
            "heating_temp_offset": 5.0,
            "device_type": "trv",
        }

        caps = DeviceCapabilities.from_dict(data)
        assert caps.supports_turn_off is False
        assert caps.device_type == "trv"
        assert caps.optimal_off_temp == 0.0


class TestDeviceProfile:
    """Test DeviceProfile dataclass."""

    def test_to_dict(self):
        """Test converting profile to dict."""
        caps = DeviceCapabilities(
            supports_turn_off=False,
            supports_turn_on=True,
            supports_temperature=True,
            supports_position=False,
            supports_hvac_modes=["heat"],
            min_temp=5.0,
            max_temp=30.0,
            temp_step=0.5,
            optimal_off_temp=0.0,
            optimal_idle_temp=10.0,
            heating_temp_offset=5.0,
            device_type="trv",
        )

        profile = DeviceProfile(
            entity_id="climate.bedroom_trv",
            capabilities=caps,
            last_discovered=datetime(2025, 12, 17, 12, 0, 0),
            discovery_method="ha_attributes",
        )

        data = profile.to_dict()
        assert data["entity_id"] == "climate.bedroom_trv"
        assert data["discovery_method"] == "ha_attributes"
        assert data["capabilities"]["device_type"] == "trv"

    def test_from_dict(self):
        """Test creating profile from dict."""
        data = {
            "entity_id": "climate.bedroom_trv",
            "capabilities": {
                "supports_turn_off": False,
                "supports_turn_on": True,
                "supports_temperature": True,
                "supports_position": False,
                "supports_hvac_modes": ["heat"],
                "min_temp": 5.0,
                "max_temp": 30.0,
                "temp_step": 0.5,
                "optimal_off_temp": 0.0,
                "optimal_idle_temp": 10.0,
                "heating_temp_offset": 5.0,
                "device_type": "trv",
            },
            "last_discovered": "2025-12-17T12:00:00",
            "discovery_method": "ha_attributes",
        }

        profile = DeviceProfile.from_dict(data)
        assert profile.entity_id == "climate.bedroom_trv"
        assert profile.capabilities.device_type == "trv"


class TestDeviceCapabilityDetector:
    """Test DeviceCapabilityDetector class."""

    def test_detect_device_type_trv(self, detector):
        """Test detecting TRV device type."""
        state = MagicMock(spec=State)
        state.attributes = {"hvac_modes": ["heat", "off"]}

        # Test Dutch TRV pattern
        assert (
            detector._detect_device_type("climate.slaapkamer_radiatorknop", state, "mqtt") == "trv"
        )

        # Test English TRV pattern
        assert detector._detect_device_type("climate.bedroom_trv", state, "zigbee") == "trv"

        # Test valve pattern
        assert detector._detect_device_type("climate.radiator_valve", state, "mqtt") == "trv"

    def test_detect_device_type_ac(self, detector):
        """Test detecting AC unit type."""
        state = MagicMock(spec=State)
        state.attributes = {
            "hvac_modes": ["heat", "cool", "off"],
            "device_class": "ac",
        }

        assert detector._detect_device_type("climate.living_room_ac", state, "mqtt") == "ac_unit"

    def test_detect_device_type_thermostat(self, detector):
        """Test detecting regular thermostat."""
        state = MagicMock(spec=State)
        state.attributes = {"hvac_modes": ["heat", "off"]}

        assert (
            detector._detect_device_type("climate.hallway_thermostat", state, "mqtt")
            == "thermostat"
        )

    def test_get_optimal_parameters_trv(self, detector):
        """Test getting optimal parameters for TRV."""
        params = detector._get_optimal_parameters("trv")

        assert params["off_temp"] == 0.0
        assert params["idle_temp"] == 10.0
        assert params["heating_offset"] == 5.0

    def test_get_optimal_parameters_ac(self, detector):
        """Test getting optimal parameters for AC."""
        params = detector._get_optimal_parameters("ac_unit")

        assert params["off_temp"] is None
        assert params["idle_temp"] is None
        assert params["heating_offset"] == 0.0

    def test_get_optimal_parameters_thermostat(self, detector):
        """Test getting optimal parameters for thermostat."""
        params = detector._get_optimal_parameters("thermostat")

        assert params["off_temp"] == 5.0  # Frost protection temp
        assert params["idle_temp"] is None
        assert params["heating_offset"] == 0.0

    @pytest.mark.asyncio
    async def test_discover_climate_device_trv(self, detector, mock_hass):
        """Test discovering a TRV device."""
        # Mock state
        state = MagicMock(spec=State)
        state.attributes = {
            "supported_features": 1,  # SUPPORT_TARGET_TEMPERATURE
            "hvac_modes": ["heat", "off"],
            "min_temp": 5.0,
            "max_temp": 30.0,
            "target_temp_step": 0.5,
        }
        mock_hass.states.get.return_value = state

        # Mock entity/device registry
        with patch("smart_heating.features.device_capability_detector.er.async_get") as mock_er:
            with patch("smart_heating.features.device_capability_detector.dr.async_get") as mock_dr:
                mock_er.return_value.async_get.return_value = None
                mock_dr.return_value.async_get.return_value = None

                profile = await detector.discover_climate_device("climate.bedroom_radiatorknop")

                assert profile.entity_id == "climate.bedroom_radiatorknop"
                assert profile.capabilities.device_type == "trv"
                assert profile.capabilities.supports_turn_off is False
                assert profile.capabilities.supports_temperature is True
                assert profile.capabilities.optimal_off_temp == 0.0
                assert profile.capabilities.optimal_idle_temp == 10.0
                assert profile.capabilities.heating_temp_offset == 5.0
                assert profile.discovery_method == "ha_attributes"

    @pytest.mark.asyncio
    async def test_discover_and_cache(self, detector, mock_hass):
        """Test discovering and caching a device."""
        state = MagicMock(spec=State)
        state.attributes = {
            "supported_features": 1,
            "hvac_modes": ["heat", "off"],
            "min_temp": 5.0,
            "max_temp": 30.0,
        }
        mock_hass.states.get.return_value = state

        with patch("smart_heating.features.device_capability_detector.er.async_get") as mock_er:
            with patch("smart_heating.features.device_capability_detector.dr.async_get") as mock_dr:
                mock_er.return_value.async_get.return_value = None
                mock_dr.return_value.async_get.return_value = None

                # The discovery is performed and cached; we don't need the return value here
                await detector.discover_and_cache("climate.test_trv")

                # Check cached
                cached = detector.get_profile("climate.test_trv")
                assert cached is not None
                assert cached.entity_id == "climate.test_trv"

    def test_load_profiles(self, detector):
        """Test loading profiles from storage."""
        profiles_data = {
            "climate.bedroom_trv": {
                "entity_id": "climate.bedroom_trv",
                "capabilities": {
                    "supports_turn_off": False,
                    "supports_turn_on": True,
                    "supports_temperature": True,
                    "supports_position": False,
                    "supports_hvac_modes": ["heat"],
                    "min_temp": 5.0,
                    "max_temp": 30.0,
                    "temp_step": 0.5,
                    "optimal_off_temp": 0.0,
                    "optimal_idle_temp": 10.0,
                    "heating_temp_offset": 5.0,
                    "device_type": "trv",
                },
                "last_discovered": "2025-12-17T12:00:00",
                "discovery_method": "ha_attributes",
            }
        }

        detector.load_profiles(profiles_data)

        profile = detector.get_profile("climate.bedroom_trv")
        assert profile is not None
        assert profile.capabilities.device_type == "trv"

    def test_get_all_profiles(self, detector):
        """Test getting all profiles for storage."""
        # Add some profiles
        caps = DeviceCapabilities(
            supports_turn_off=False,
            supports_turn_on=True,
            supports_temperature=True,
            supports_position=False,
            supports_hvac_modes=["heat"],
            min_temp=5.0,
            max_temp=30.0,
            temp_step=0.5,
            optimal_off_temp=0.0,
            optimal_idle_temp=10.0,
            heating_temp_offset=5.0,
            device_type="trv",
        )

        profile = DeviceProfile(
            entity_id="climate.test",
            capabilities=caps,
            last_discovered=datetime.now(),
            discovery_method="ha_attributes",
        )

        detector._profiles["climate.test"] = profile

        all_profiles = detector.get_all_profiles()
        assert "climate.test" in all_profiles
        assert all_profiles["climate.test"]["entity_id"] == "climate.test"

    def test_find_related_entities(self, detector, mock_hass):
        """Test finding related entities."""
        # Mock state.get to return power switch
        mock_hass.states.get.side_effect = lambda entity_id: (
            MagicMock() if entity_id == "switch.bedroom_trv_power" else None
        )

        related = detector._find_related_entities("climate.bedroom_trv")

        assert related["power_switch"] == "switch.bedroom_trv_power"
        assert related["valve_position"] is None

    @pytest.mark.asyncio
    async def test_discover_climate_device_not_found(self, detector, mock_hass):
        """Test discovering a device that doesn't exist."""
        mock_hass.states.get.return_value = None

        with pytest.raises(ValueError, match="Entity .* not found"):
            await detector.discover_climate_device("climate.nonexistent")
