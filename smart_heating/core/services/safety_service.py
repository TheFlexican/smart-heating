"""Safety sensor monitoring service for Smart Heating integration."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class SafetyService:
    """Handles safety sensor monitoring and alert management."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize safety service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._safety_sensors: list[dict[str, Any]] = []
        self._safety_alert_active: bool = False
        self._safety_state_unsub = None  # State listener unsubscribe callback

        # Legacy single sensor fields (for backwards compatibility)
        self.safety_sensor_id: str | None = None
        self.safety_sensor_attribute: str = "smoke"
        self.safety_sensor_alert_value: str | bool = True
        self.safety_sensor_enabled: bool = True

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
        for sensor in self._safety_sensors:
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
        self._safety_sensors.append(
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
        self._safety_sensors = [s for s in self._safety_sensors if s["sensor_id"] != sensor_id]
        # Clear alert if no sensors remain
        if not self._safety_sensors:
            self._safety_alert_active = False
        _LOGGER.info("Safety sensor removed: %s", sensor_id)

    def get_safety_sensors(self) -> list[dict[str, Any]]:
        """Get all configured safety sensors.

        Returns:
            List of safety sensor configurations
        """
        return self._safety_sensors.copy()

    def clear_safety_sensors(self) -> None:
        """Clear all configured safety sensors."""
        self._safety_sensors = []
        self._safety_alert_active = False
        _LOGGER.info("Cleared all safety sensors")

    def check_safety_sensor_status(self) -> tuple[bool, str | None]:
        """Check if any safety sensor is in alert state.

        Returns:
            Tuple of (is_alert, sensor_id) - True if any sensor is alerting, with the sensor ID
        """
        if not self._safety_sensors:
            return False, None

        for sensor in self._safety_sensors:
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

    def load_safety_config(self, data: dict[str, Any]) -> None:
        """Load safety sensor configuration from storage.

        Args:
            data: Configuration dictionary from storage
        """
        # Load safety sensor configuration
        if "safety_sensors" in data:
            self._safety_sensors = data.get("safety_sensors", [])
        elif data.get("safety_sensor_id"):
            # Migrate old single sensor format to new list format
            _LOGGER.info("Migrating old safety sensor format to new multi-sensor format")
            self._safety_sensors = [
                {
                    "sensor_id": data.get("safety_sensor_id"),
                    "attribute": data.get("safety_sensor_attribute", "smoke"),
                    "alert_value": data.get("safety_sensor_alert_value", True),
                    "enabled": data.get("safety_sensor_enabled", True),
                }
            ]
        else:
            self._safety_sensors = []
        self._safety_alert_active = data.get("safety_alert_active", False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize safety sensor configuration to dictionary.

        Returns:
            Dictionary with safety sensor configuration
        """
        return {
            "safety_sensors": self._safety_sensors,
            "safety_alert_active": self._safety_alert_active,
        }
