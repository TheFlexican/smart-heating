"""Base handler for device control operations."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from homeassistant.core import HomeAssistant

from ...const import TEMP_COMPARISON_TOLERANCE
from ...models import DeviceEvent

if TYPE_CHECKING:
    from ...area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


class BaseDeviceHandler:
    """Base class for device handlers with shared utilities."""

    def __init__(
        self,
        hass: HomeAssistant,
        area_manager: "AreaManager",
        capability_detector=None,
    ):
        """Initialize base device handler.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            capability_detector: DeviceCapabilityDetector instance (optional)
        """
        self.hass = hass
        self.area_manager = area_manager
        self.capability_detector = capability_detector
        self._device_capabilities: dict[str, dict[str, Any]] = {}

    def _is_trv_device(self, entity_id: str) -> bool:
        """Detect if a climate entity is a TRV (Thermostatic Radiator Valve).

        Uses capability detector if available, falls back to pattern matching.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if entity appears to be a TRV device
        """
        # Use capability detector if available
        if self.capability_detector:
            profile = self.capability_detector.get_profile(entity_id)
            if profile:
                is_trv = profile.capabilities.device_type == "trv"
                _LOGGER.debug(
                    "TRV detection via capability detector: %s -> %s (device_type=%s)",
                    entity_id,
                    is_trv,
                    profile.capabilities.device_type,
                )
                return is_trv

        # Fallback to pattern matching
        trv_patterns = [
            "radiatorknop",  # Dutch TRVs
            "radiator_knop",
            "trv",
            "radiator_valve",
            "thermostatic_valve",
            "valve",
        ]
        entity_lower = entity_id.lower()
        is_trv = any(pattern in entity_lower for pattern in trv_patterns)
        _LOGGER.warning(
            "TRV detection via pattern matching: %s -> %s",
            entity_id,
            is_trv,
        )
        return is_trv

    def _power_switch_patterns(self, base_name: str) -> list[str]:
        """Return common power switch patterns for a climate base name.

        This consolidates duplicated patterns used when detecting a power switch
        for climate entities (e.g., switch.<base>_power, switch.<base>_switch).
        """
        return [f"switch.{base_name}_power", f"switch.{base_name}_switch", f"switch.{base_name}"]

    def _get_thermostat_state(self, thermostat_id: str) -> tuple[Optional[str], Optional[float]]:
        """Return (hvac_mode, temperature) for a thermostat if available.

        For Home Assistant climate entities, hvac_mode is the entity state itself
        (state.state), not an attribute.
        """
        state = self.hass.states.get(thermostat_id)
        current_hvac_mode = None
        current_temp = None
        if state:
            try:
                # hvac_mode IS the state for climate entities (heat, cool, off, etc.)
                if state.state not in ("unknown", "unavailable", None):
                    current_hvac_mode = state.state
                # target temperature is in attributes
                if hasattr(state, "attributes"):
                    current_temp = state.attributes.get("temperature")
            except (AttributeError, TypeError):
                # Handle test mocks that don't have proper attributes
                pass
        return current_hvac_mode, current_temp

    def _should_update_temperature(
        self, current_temp: Optional[float], last_temp: Optional[float], target_temp: float
    ) -> bool:
        """Return True when temperature should be updated based on current and last set values."""
        try:
            if current_temp is not None and isinstance(current_temp, (int, float)):
                if abs(current_temp - target_temp) < TEMP_COMPARISON_TOLERANCE:
                    return False
            if last_temp is not None and abs(last_temp - target_temp) < TEMP_COMPARISON_TOLERANCE:
                return False
        except (TypeError, AttributeError):
            # Handle test mocks or invalid values
            return True

        return True

    def _record_device_event(
        self,
        device_id: str,
        direction: str,
        command_type: str,
        payload: Any | None = None,
        status: str | None = None,
        error: str | None = None,
    ) -> None:
        """Record a device event into the AreaManager log (best-effort).

        This constructs a `DeviceEvent` model and appends it to the area manager's
        device log for the relevant area(s). Failures are swallowed to avoid
        impacting device control flows.
        """
        try:
            # Resolve area id if available on area_manager (best-effort)
            area_id = getattr(self.area_manager, "current_area_id", None)
            if not area_id:
                # If area_id cannot be resolved, try to find by device mapping
                try:
                    area_id = self.area_manager.find_area_by_device(device_id)
                except Exception:
                    area_id = ""

            from ...models import DeviceEvent

            evt = DeviceEvent.now(
                area_id=area_id or "",
                device_id=device_id,
                direction=direction,
                command_type=command_type,
                payload=payload or {},
                status=status,
                error=error,
            )

            try:
                self.area_manager.async_add_device_event(area_id or "", evt)
            except Exception:
                # Best-effort: ignore logging failures
                _LOGGER.debug("Failed to append device event for %s", device_id)
        except Exception as err:
            # Never raise from logging helper
            _LOGGER.debug("_record_device_event failed for %s: %s", device_id, err)
