"""Valve device handler for position and temperature control."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate.const import SERVICE_SET_TEMPERATURE
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.exceptions import HomeAssistantError

from ...exceptions import DeviceError
from .base_device_handler import BaseDeviceHandler

if TYPE_CHECKING:
    from ...models import Area

_LOGGER = logging.getLogger(__name__)

# Service constants
SERVICE_NUMBER_SET_VALUE = "number.set_value"
SERVICE_CLIMATE_SET_POSITION = "climate.set_position"
SERVICE_CLIMATE_SET_TEMPERATURE = "climate.set_temperature"


class ValveHandler(BaseDeviceHandler):
    """Handle valve/TRV device operations."""

    def get_valve_capability(self, entity_id: str) -> dict[str, Any]:
        """Get valve control capabilities from HA entity.

        Works with ANY valve from ANY manufacturer by querying entity attributes.

        Args:
            entity_id: Entity ID of the valve

        Returns:
            Dict with capability information
        """
        # Check cache first
        if entity_id in self._device_capabilities:
            return self._device_capabilities[entity_id]

        capabilities = {
            "supports_position": False,
            "supports_temperature": False,
            "position_min": 0,
            "position_max": 100,
            "entity_domain": entity_id.split(".")[0] if "." in entity_id else "unknown",
        }

        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Cannot determine capabilities for %s: entity not found", entity_id)
            self._device_capabilities[entity_id] = capabilities
            return capabilities

        # Check entity domain
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        capabilities["entity_domain"] = domain

        if domain == "number":
            # number.* entities support position control
            capabilities["supports_position"] = True
            capabilities["position_min"] = state.attributes.get("min", 0)
            capabilities["position_max"] = state.attributes.get("max", 100)
            _LOGGER.debug(
                "Valve %s supports position control (range: %s-%s)",
                entity_id,
                capabilities["position_min"],
                capabilities["position_max"],
            )

        elif domain == "climate":
            # climate.* entities - check if they have position attribute
            if "position" in state.attributes:
                capabilities["supports_position"] = True
                _LOGGER.debug(
                    "Valve %s (climate) supports position control via attribute",
                    entity_id,
                )

            # Check if it supports temperature
            if "temperature" in state.attributes or "target_temp_low" in state.attributes:
                capabilities["supports_temperature"] = True
                _LOGGER.debug("Valve %s supports temperature control", entity_id)

        # Cache the result
        self._device_capabilities[entity_id] = capabilities
        return capabilities

    async def async_control_valves(
        self, area: "Area", heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control valves/TRVs in an area."""
        valves = area.get_valves()

        for valve_id in valves:
            try:
                capabilities = self.get_valve_capability(valve_id)

                # Prefer position control if available
                if capabilities["supports_position"]:
                    await self._control_valve_by_position(valve_id, capabilities, heating)

                # Fall back to temperature control
                if not capabilities["supports_position"] and capabilities["supports_temperature"]:
                    await self._control_valve_by_temperature(valve_id, heating, target_temp)

                if (
                    not capabilities["supports_position"]
                    and not capabilities["supports_temperature"]
                ):
                    _LOGGER.warning(
                        "Valve %s doesn't support position or temperature control",
                        valve_id,
                    )

            except (HomeAssistantError, DeviceError) as err:
                _LOGGER.error(
                    "Failed to control valve %s: %s",
                    valve_id,
                    err,
                    exc_info=True,
                )
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout controlling valve %s", valve_id, exc_info=True)

    async def _control_valve_by_position(
        self, valve_id: str, capabilities: dict, heating: bool
    ) -> None:
        """Control valve using position control (number or climate entity)."""
        domain = capabilities["entity_domain"]

        if domain == "number":
            position = capabilities["position_max"] if heating else capabilities["position_min"]
            await self._set_valve_number_position(valve_id, position)
            action = "Opened" if heating else "Closed"
            _LOGGER.debug(f"{action} valve %s to %.0f%%", valve_id, position)

        elif domain == "climate" and "position" in self.hass.states.get(valve_id).attributes:
            position = capabilities["position_max"] if heating else capabilities["position_min"]
            try:
                await self._set_valve_climate_position(valve_id, position)
                _LOGGER.debug("Set valve %s position to %.0f%%", valve_id, position)
            except (HomeAssistantError, DeviceError):
                _LOGGER.debug(
                    "Valve %s doesn't support set_position, using temperature control",
                    valve_id,
                )
                capabilities["supports_position"] = False
                capabilities["supports_temperature"] = True

    async def _control_valve_by_temperature(
        self, valve_id: str, heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control valve using temperature control."""
        if heating and target_temp is not None:
            # For TRV devices, apply configured heating temp and offset:
            # Use max(target + offset, configured_trv_heating_temp)
            if self._is_trv_device(valve_id):
                trv_temp = max(
                    target_temp + getattr(self.area_manager, "trv_temp_offset", 0.0),
                    getattr(self.area_manager, "trv_heating_temp", target_temp),
                )
                await self._set_valve_temperature(valve_id, trv_temp)
                _LOGGER.debug(
                    "Set TRV %s to %.1f°C (heating - applied offset/limit)", valve_id, trv_temp
                )
            else:
                # Non-TRV temperature-controlled valves: set to area target temperature
                await self._set_valve_temperature(valve_id, target_temp)
                _LOGGER.debug("Set valve %s to area target %.1f°C", valve_id, target_temp)
        else:
            # When not heating: for TRVs use configured idle temp, otherwise set to 0°C
            if self._is_trv_device(valve_id):
                idle = getattr(self.area_manager, "trv_idle_temp", 0.0)
                await self._set_valve_temperature(valve_id, idle)
                _LOGGER.debug("Set TRV %s to %.1f°C (idle)", valve_id, idle)
            else:
                await self._set_valve_temperature(valve_id, 0.0)
                _LOGGER.debug("Set valve %s to 0°C (off)", valve_id)

    async def _set_valve_number_position(self, valve_id: str, position: float) -> None:
        try:
            payload = {"entity_id": valve_id, "value": position}
            try:
                self._record_device_event(
                    valve_id,
                    "sent",
                    SERVICE_NUMBER_SET_VALUE,
                    {"domain": "number", "service": "set_value", "data": payload},
                )
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                _LOGGER.debug(
                    "Failed to record sent SERVICE_NUMBER_SET_VALUE for %s: %s", valve_id, err
                )

            await self.hass.services.async_call(
                "number",
                "set_value",
                payload,
                blocking=False,
            )
            try:
                self._record_device_event(
                    valve_id, "received", SERVICE_NUMBER_SET_VALUE, {"result": "dispatched"}
                )
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                _LOGGER.debug(
                    "Failed to record received SERVICE_NUMBER_SET_VALUE for %s: %s", valve_id, err
                )
        except (HomeAssistantError, asyncio.TimeoutError) as err:
            try:
                self._record_device_event(
                    valve_id,
                    "received",
                    SERVICE_NUMBER_SET_VALUE,
                    {"result": "error"},
                    status="error",
                    error=str(err),
                )
            except (AttributeError, KeyError, TypeError, ValueError) as record_err:
                _LOGGER.debug(
                    "Failed to record error for SERVICE_NUMBER_SET_VALUE %s: %s",
                    valve_id,
                    record_err,
                )
            _LOGGER.error(
                "Failed to set valve number position %s: %s", valve_id, err, exc_info=True
            )
            raise DeviceError(f"Failed to set valve {valve_id} position: {err}") from err

    async def _set_valve_climate_position(self, valve_id: str, position: float) -> None:
        try:
            payload = {"entity_id": valve_id, "position": position}
            try:
                self._record_device_event(
                    valve_id,
                    "sent",
                    SERVICE_CLIMATE_SET_POSITION,
                    {"domain": CLIMATE_DOMAIN, "service": "set_position", "data": payload},
                )
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                _LOGGER.debug(
                    "Failed to record sent SERVICE_CLIMATE_SET_POSITION for %s: %s", valve_id, err
                )

            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                "set_position",
                payload,
                blocking=False,
            )
            try:
                self._record_device_event(
                    valve_id, "received", SERVICE_CLIMATE_SET_POSITION, {"result": "dispatched"}
                )
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                _LOGGER.debug(
                    "Failed to record received SERVICE_CLIMATE_SET_POSITION for %s: %s",
                    valve_id,
                    err,
                )
        except (HomeAssistantError, asyncio.TimeoutError) as err:
            try:
                self._record_device_event(
                    valve_id,
                    "received",
                    SERVICE_CLIMATE_SET_POSITION,
                    {"result": "error"},
                    status="error",
                    error=str(err),
                )
            except (AttributeError, KeyError, TypeError, ValueError) as record_err:
                _LOGGER.debug(
                    "Failed to record error for SERVICE_CLIMATE_SET_POSITION %s: %s",
                    valve_id,
                    record_err,
                )
            _LOGGER.error(
                "Failed to set valve climate position %s: %s", valve_id, err, exc_info=True
            )
            # Re-raise so callers (which may attempt fallback) can detect failure
            raise DeviceError(f"Failed to set valve {valve_id} climate position: {err}") from err

    async def _set_valve_temperature(self, valve_id: str, temperature: float) -> None:
        try:
            payload = {"entity_id": valve_id, ATTR_TEMPERATURE: temperature}
            try:
                self._record_device_event(
                    valve_id,
                    "sent",
                    SERVICE_CLIMATE_SET_TEMPERATURE,
                    {"domain": CLIMATE_DOMAIN, "service": SERVICE_SET_TEMPERATURE, "data": payload},
                )
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                _LOGGER.debug("Failed to record sent set_temperature for %s: %s", valve_id, err)

            await self.hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                payload,
                blocking=False,
            )
            try:
                self._record_device_event(
                    valve_id, "received", SERVICE_CLIMATE_SET_TEMPERATURE, {"result": "dispatched"}
                )
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                _LOGGER.debug("Failed to record received set_temperature for %s: %s", valve_id, err)
        except (HomeAssistantError, asyncio.TimeoutError) as err:
            try:
                self._record_device_event(
                    valve_id,
                    "received",
                    SERVICE_CLIMATE_SET_TEMPERATURE,
                    {"result": "error"},
                    status="error",
                    error=str(err),
                )
            except (AttributeError, KeyError, TypeError, ValueError) as record_err:
                _LOGGER.debug(
                    "Failed to record error for set_temperature %s: %s", valve_id, record_err
                )
            _LOGGER.error("Failed to set valve temperature %s: %s", valve_id, err, exc_info=True)
            raise DeviceError(f"Failed to set valve {valve_id} temperature: {err}") from err

    async def async_set_valves_to_off(self, area: "Area", off_temperature: float = 0.0) -> None:
        """Set all valves in an area to an "off" state.

        For position-controlled valves this sets them to the minimum position.
        For temperature-controlled valves this sets the temperature to the provided
        off_temperature (defaults to 0.0°C which instructs TRVs to close).
        """
        valves = area.get_valves()

        for valve_id in valves:
            try:
                caps = self.get_valve_capability(valve_id)

                # Prefer position control where available
                if caps.get("supports_position"):
                    # Set to minimum position (closed)
                    position = caps.get("position_min", 0)
                    if caps.get("entity_domain") == "number":
                        await self._set_valve_number_position(valve_id, position)
                    else:
                        # climate with position attribute
                        try:
                            await self._set_valve_climate_position(valve_id, position)
                        except DeviceError:
                            # Fallback to temperature control
                            _LOGGER.debug(
                                "Climate position failed for %s, falling back to temperature control",
                                valve_id,
                            )
                            await self._set_valve_temperature(valve_id, off_temperature)

                elif caps.get("supports_temperature"):
                    # Temperature-controlled TRV: set to off_temperature (0°C by default)
                    await self._set_valve_temperature(valve_id, off_temperature)
                else:
                    _LOGGER.warning(
                        "Valve %s doesn't support position or temperature control - cannot reliably turn off",
                        valve_id,
                    )
            except (HomeAssistantError, DeviceError) as err:
                _LOGGER.error(
                    "Failed to set valve %s to off: %s",
                    valve_id,
                    err,
                    exc_info=True,
                )
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout setting valve %s to off", valve_id, exc_info=True)
