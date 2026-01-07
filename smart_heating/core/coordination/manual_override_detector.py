"""Manual override detector for Smart Heating integration."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...models import Area
    from ..area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


class ManualOverrideDetector:
    """Detects and handles manual temperature overrides.

    Extracts manual override detection logic from Coordinator._apply_manual_temperature_change.

    This component:
    - Detects when a user manually changes a thermostat temperature
    - Distinguishes manual changes from automated schedule/preset changes
    - Filters out stale state changes to prevent false positives
    - Manages the manual override flag on areas
    """

    def __init__(self, startup_grace_period_active: bool = False) -> None:
        """Initialize manual override detector.

        Args:
            startup_grace_period_active: Whether startup grace period is active
        """
        self._startup_grace_period = startup_grace_period_active

    def set_startup_grace_period(self, active: bool) -> None:
        """Set the startup grace period state.

        Args:
            active: Whether startup grace period is active
        """
        self._startup_grace_period = active
        if not active:
            _LOGGER.info("Startup grace period ended - manual override detection now active")

    async def async_detect_and_apply_override(
        self,
        entity_id: str,
        new_temp: float | None,
        area_manager: "AreaManager",
    ) -> bool:
        """Detect if temperature change is manual override and apply it.

        Args:
            entity_id: Thermostat entity ID
            new_temp: New temperature set by user
            area_manager: Area manager instance

        Returns:
            True if manual override was detected and applied, False otherwise
        """
        # Skip manual override detection during startup grace period
        if self._startup_grace_period:
            _LOGGER.info(
                "Temperature change for %s ignored - still in startup grace period",
                entity_id,
            )
            return False

        # Skip if temperature is None (some devices report None during state changes)
        if new_temp is None:
            _LOGGER.debug(
                "Temperature change for %s is None - ignoring",
                entity_id,
            )
            return False

        # Find the area containing this thermostat
        area = self._find_area_for_device(entity_id, area_manager)
        if not area:
            _LOGGER.debug("No area found for device %s", entity_id)
            return False

        # Check if this is truly a manual change
        if not self._is_manual_change(entity_id, new_temp, area):
            return False

        # Apply manual override
        await self._apply_override(entity_id, new_temp, area, area_manager)
        return True

    def _find_area_for_device(
        self,
        entity_id: str,
        area_manager: "AreaManager",
    ) -> "Area | None":
        """Find the area containing the specified device.

        Args:
            entity_id: Device entity ID
            area_manager: Area manager instance

        Returns:
            Area containing the device, or None
        """
        for area in area_manager.get_all_areas().values():
            if entity_id in area.devices:
                return area
        return None

    def _is_manual_change(
        self,
        _entity_id: str,
        new_temp: float,
        area: "Area",
    ) -> bool:
        """Determine if temperature change is a manual user change.

        This filters out:
        - Changes that match the expected target (from schedules/presets)
        - Stale changes that are lower than current target
        - Idle state setpoint changes (when system sets thermostat to current_temp)

        Args:
            _entity_id: Thermostat entity ID (unused, kept for API consistency)
            new_temp: New temperature
            area: Area instance

        Returns:
            True if this is a manual change, False otherwise
        """
        expected_temp = area.get_effective_target_temperature()

        # Allow 0.1°C tolerance for floating point comparison
        if abs(new_temp - expected_temp) < 0.1:
            _LOGGER.info(
                "Temperature change for %s matches expected %.1f°C - ignoring (not manual)",
                area.name,
                expected_temp,
            )
            return False

        # IMPORTANT: Ignore temperature changes that are LOWER than current target
        # These are typically stale state changes from old preset values that arrive
        # AFTER a schedule has already updated the area target to a higher value.
        # This prevents false manual override triggers during schedule transitions.
        if new_temp < expected_temp - 0.1:
            _LOGGER.info(
                "Temperature change for %s is %.1f°C < expected %.1f°C - likely stale state from old preset, ignoring",
                area.name,
                new_temp,
                expected_temp,
            )
            return False

        # Check if this could be an automated idle setpoint adjustment
        # During idle states, the system may set thermostat to current_temp
        # if current_temp >= (target - hysteresis) to prevent unnecessary cycling
        if self._is_likely_idle_setpoint_adjustment(new_temp, expected_temp, area):
            return False

        return True

    def _is_likely_idle_setpoint_adjustment(
        self,
        new_temp: float,
        expected_temp: float,
        area: "Area",
    ) -> bool:
        """Check if temperature change is likely an automated idle setpoint adjustment.

        During idle states, the temperature setter may set the thermostat to current_temp
        if current_temp is at or above (target - hysteresis). This prevents the system
        from incorrectly detecting this as a manual override.

        The idle setpoint logic in temperature_setter.py:
        - Sets thermostat to current_temp when current_temp >= (target - hysteresis)
        - This prevents unnecessary heating cycles when room is already warm enough

        Args:
            new_temp: New temperature that was set
            expected_temp: Expected target temperature from schedule/preset
            area: Area instance

        Returns:
            True if this looks like an idle setpoint adjustment, False otherwise
        """
        current_temp = area.current_temperature
        if current_temp is None:
            return False

        # Ensure current_temp is a number (not a mock or other object)
        try:
            current_temp = float(current_temp)
        except (TypeError, ValueError):
            return False

        # Get hysteresis value for this area
        hysteresis = self._get_hysteresis(area)

        # Check if new_temp matches current_temp (within tolerance)
        temp_matches_current = abs(new_temp - current_temp) < 0.15

        # The idle setpoint logic sets thermostat to current_temp when:
        # current_temp >= (target - hysteresis)
        # So we should accept ANY current_temp that is >= (target - hysteresis)
        # This includes temperatures ABOVE the target (room is warmer than needed)
        current_above_threshold = current_temp >= (expected_temp - hysteresis - 0.1)

        if temp_matches_current and current_above_threshold:
            _LOGGER.info(
                "Temperature change for %s to %.1f°C matches current temp %.1f°C "
                "(>= threshold %.1f°C) - ignoring (likely automated idle setpoint adjustment)",
                area.name,
                new_temp,
                current_temp,
                expected_temp - hysteresis,
            )
            return True

        return False

    def _get_hysteresis(self, area: "Area") -> float:
        """Get the hysteresis value for an area.

        Args:
            area: Area instance

        Returns:
            Hysteresis value in degrees Celsius
        """
        # Check for area-specific hysteresis override
        if hasattr(area, "hysteresis_override") and area.hysteresis_override is not None:
            try:
                return float(area.hysteresis_override)
            except (TypeError, ValueError):
                pass

        # Fall back to global hysteresis from area manager
        if hasattr(area, "area_manager") and area.area_manager is not None:
            if hasattr(area.area_manager, "hysteresis"):
                try:
                    return float(area.area_manager.hysteresis)
                except (TypeError, ValueError):
                    pass

        # Default hysteresis
        return 0.5

    async def _apply_override(
        self,
        _entity_id: str,
        new_temp: float,
        area: "Area",
        area_manager: "AreaManager",
    ) -> None:
        """Apply manual override to the area.

        Args:
            _entity_id: Thermostat entity ID (unused, kept for API consistency)
            new_temp: New temperature
            area: Area instance
            area_manager: Area manager instance
        """
        expected_temp = area.get_effective_target_temperature()

        # This is a true manual change - enter manual override mode
        _LOGGER.warning(
            "Area %s entering MANUAL OVERRIDE mode - thermostat changed to %.1f°C (expected %.1f°C)",
            area.name,
            new_temp,
            expected_temp,
        )
        area.target_temperature = new_temp
        area.manual_override = True  # Enter manual override mode

        # Save to storage so it persists across restarts
        await area_manager.async_save()
