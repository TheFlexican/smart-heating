"""Test SafetyService functionality."""

import pytest
from unittest.mock import Mock

from smart_heating.core.services.safety_service import SafetyService


class TestSafetyService:
    """Test SafetyService functionality."""

    def test_init(self, mock_hass):
        """Test SafetyService initialization."""
        service = SafetyService(mock_hass)

        assert service.hass == mock_hass
        assert service._safety_sensors == []
        assert service._safety_alert_active is False
        assert service._safety_state_unsub is None

    def test_add_safety_sensor(self, mock_hass):
        """Test adding a safety sensor."""
        service = SafetyService(mock_hass)

        service.add_safety_sensor(
            sensor_id="binary_sensor.smoke",
            attribute="state",
            alert_value="on",
            enabled=True,
        )

        sensors = service.get_safety_sensors()
        assert len(sensors) == 1
        assert sensors[0]["sensor_id"] == "binary_sensor.smoke"
        assert sensors[0]["attribute"] == "state"
        assert sensors[0]["alert_value"] == "on"
        assert sensors[0]["enabled"] is True

    def test_add_duplicate_safety_sensor(self, mock_hass):
        """Test adding duplicate sensor updates existing one."""
        service = SafetyService(mock_hass)

        # Add initial sensor
        service.add_safety_sensor(
            sensor_id="binary_sensor.smoke",
            attribute="state",
            alert_value="on",
            enabled=True,
        )

        # Add same sensor with different settings
        service.add_safety_sensor(
            sensor_id="binary_sensor.smoke",
            attribute="smoke",
            alert_value=True,
            enabled=False,
        )

        sensors = service.get_safety_sensors()
        assert len(sensors) == 1  # Should still be only one sensor
        assert sensors[0]["attribute"] == "smoke"  # Should be updated
        assert sensors[0]["alert_value"] is True  # Should be updated
        assert sensors[0]["enabled"] is False  # Should be updated

    def test_remove_safety_sensor(self, mock_hass):
        """Test removing a safety sensor."""
        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)
        service.add_safety_sensor("binary_sensor.co", "state", "on", True)

        assert len(service.get_safety_sensors()) == 2

        service.remove_safety_sensor("binary_sensor.smoke")

        sensors = service.get_safety_sensors()
        assert len(sensors) == 1
        assert sensors[0]["sensor_id"] == "binary_sensor.co"

    def test_remove_last_sensor_clears_alert(self, mock_hass):
        """Test removing last sensor clears alert state."""
        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)
        service.set_safety_alert_active(True)

        assert service.is_safety_alert_active() is True

        service.remove_safety_sensor("binary_sensor.smoke")

        assert service.is_safety_alert_active() is False

    def test_get_safety_sensors_returns_copy(self, mock_hass):
        """Test get_safety_sensors returns a copy."""
        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)

        sensors = service.get_safety_sensors()
        sensors.append({"sensor_id": "fake"})

        # Original should be unchanged
        assert len(service.get_safety_sensors()) == 1

    def test_clear_safety_sensors(self, mock_hass):
        """Test clearing all safety sensors."""
        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)
        service.add_safety_sensor("binary_sensor.co", "state", "on", True)
        service.set_safety_alert_active(True)

        service.clear_safety_sensors()

        assert len(service.get_safety_sensors()) == 0
        assert service.is_safety_alert_active() is False

    def test_check_safety_sensor_status_no_sensors(self, mock_hass):
        """Test checking status with no sensors."""
        service = SafetyService(mock_hass)

        is_alert, sensor_id = service.check_safety_sensor_status()

        assert is_alert is False
        assert sensor_id is None

    def test_check_safety_sensor_status_not_alerting(self, mock_hass):
        """Test checking status when sensors are not alerting."""
        # Configure states mock
        from unittest.mock import MagicMock

        mock_hass.states = MagicMock()

        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)

        # Mock state as safe
        safe_state = Mock()
        safe_state.state = "off"
        safe_state.attributes = {}
        mock_hass.states.get.return_value = safe_state

        is_alert, sensor_id = service.check_safety_sensor_status()

        assert is_alert is False
        assert sensor_id is None

    def test_check_safety_sensor_status_alerting(self, mock_hass):
        """Test checking status when sensor is alerting."""
        # Configure states mock
        from unittest.mock import MagicMock

        mock_hass.states = MagicMock()

        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)

        # Mock state as alerting
        alert_state = Mock()
        alert_state.state = "on"
        alert_state.attributes = {}
        mock_hass.states.get.return_value = alert_state

        is_alert, sensor_id = service.check_safety_sensor_status()

        assert is_alert is True
        assert sensor_id == "binary_sensor.smoke"

    def test_check_safety_sensor_status_attribute(self, mock_hass):
        """Test checking status using attribute instead of state."""
        # Configure states mock
        from unittest.mock import MagicMock

        mock_hass.states = MagicMock()

        service = SafetyService(mock_hass)

        service.add_safety_sensor("sensor.detector", "smoke", True, True)

        # Mock state with attribute
        state = Mock()
        state.state = "ok"
        state.attributes = {"smoke": True}
        mock_hass.states.get.return_value = state

        is_alert, sensor_id = service.check_safety_sensor_status()

        assert is_alert is True
        assert sensor_id == "sensor.detector"

    def test_check_safety_sensor_status_disabled_sensor(self, mock_hass):
        """Test disabled sensor is ignored."""
        # Configure states mock
        from unittest.mock import MagicMock

        mock_hass.states = MagicMock()

        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", False)

        # Mock state as alerting
        alert_state = Mock()
        alert_state.state = "on"
        mock_hass.states.get.return_value = alert_state

        is_alert, sensor_id = service.check_safety_sensor_status()

        # Should not alert because sensor is disabled
        assert is_alert is False
        assert sensor_id is None

    def test_check_safety_sensor_status_missing_sensor(self, mock_hass):
        """Test sensor not found in Home Assistant."""
        # Configure states mock
        from unittest.mock import MagicMock

        mock_hass.states = MagicMock()

        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)

        # Mock state as not found
        mock_hass.states.get.return_value = None

        is_alert, sensor_id = service.check_safety_sensor_status()

        assert is_alert is False
        assert sensor_id is None

    def test_is_safety_alert_active(self, mock_hass):
        """Test checking if safety alert is active."""
        service = SafetyService(mock_hass)

        assert service.is_safety_alert_active() is False

        service.set_safety_alert_active(True)
        assert service.is_safety_alert_active() is True

        service.set_safety_alert_active(False)
        assert service.is_safety_alert_active() is False

    def test_load_safety_config_new_format(self, mock_hass):
        """Test loading safety config in new multi-sensor format."""
        service = SafetyService(mock_hass)

        config_data = {
            "safety_sensors": [
                {
                    "sensor_id": "binary_sensor.smoke",
                    "attribute": "state",
                    "alert_value": "on",
                    "enabled": True,
                },
                {
                    "sensor_id": "binary_sensor.co",
                    "attribute": "state",
                    "alert_value": "on",
                    "enabled": False,
                },
            ],
            "safety_alert_active": True,
        }

        service.load_safety_config(config_data)

        sensors = service.get_safety_sensors()
        assert len(sensors) == 2
        assert sensors[0]["sensor_id"] == "binary_sensor.smoke"
        assert sensors[1]["sensor_id"] == "binary_sensor.co"
        assert service.is_safety_alert_active() is True

    def test_load_safety_config_old_format(self, mock_hass):
        """Test loading safety config in old single-sensor format."""
        service = SafetyService(mock_hass)

        config_data = {
            "safety_sensor_id": "binary_sensor.smoke",
            "safety_sensor_attribute": "smoke",
            "safety_sensor_alert_value": True,
            "safety_sensor_enabled": True,
            "safety_alert_active": False,
        }

        service.load_safety_config(config_data)

        sensors = service.get_safety_sensors()
        assert len(sensors) == 1
        assert sensors[0]["sensor_id"] == "binary_sensor.smoke"
        assert sensors[0]["attribute"] == "smoke"
        assert sensors[0]["alert_value"] is True
        assert sensors[0]["enabled"] is True

    def test_load_safety_config_empty(self, mock_hass):
        """Test loading safety config with no data."""
        service = SafetyService(mock_hass)

        config_data = {}

        service.load_safety_config(config_data)

        assert len(service.get_safety_sensors()) == 0
        assert service.is_safety_alert_active() is False

    def test_to_dict(self, mock_hass):
        """Test serializing safety config to dict."""
        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke", "state", "on", True)
        service.set_safety_alert_active(True)

        result = service.to_dict()

        assert "safety_sensors" in result
        assert len(result["safety_sensors"]) == 1
        assert result["safety_sensors"][0]["sensor_id"] == "binary_sensor.smoke"
        assert result["safety_alert_active"] is True

    def test_multiple_sensors_first_alert_wins(self, mock_hass):
        """Test that first alerting sensor is returned."""
        # Configure states mock
        from unittest.mock import MagicMock

        mock_hass.states = MagicMock()

        service = SafetyService(mock_hass)

        service.add_safety_sensor("binary_sensor.smoke1", "state", "on", True)
        service.add_safety_sensor("binary_sensor.smoke2", "state", "on", True)

        # Create two states, both alerting
        def get_state(entity_id):
            state = Mock()
            state.state = "on"
            state.attributes = {}
            return state

        mock_hass.states.get.side_effect = get_state

        is_alert, sensor_id = service.check_safety_sensor_status()

        assert is_alert is True
        assert sensor_id == "binary_sensor.smoke1"  # First one should be returned
