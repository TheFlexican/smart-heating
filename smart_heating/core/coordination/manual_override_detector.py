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
        entity_id: str,
        new_temp: float,
        area: "Area",
    ) -> bool:
        """Determine if temperature change is a manual user change.

        This filters out:
        - Changes that match the expected target (from schedules/presets)
        - Stale changes that are lower than current target

        Args:
            entity_id: Thermostat entity ID
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

        return True

    async def _apply_override(
        self,
        entity_id: str,
        new_temp: float,
        area: "Area",
        area_manager: "AreaManager",
    ) -> None:
        """Apply manual override to the area.

        Args:
            entity_id: Thermostat entity ID
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
