"""WebSocket handler for Smart Heating."""

# Websocket helpers are exercised by integration tests and manual testing; exclude from unit coverage
# pragma: no cover

import asyncio
import logging
from typing import Any, Callable

from homeassistant.components.websocket_api import async_register_command
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.decorators import websocket_command
from homeassistant.components.websocket_api.messages import result_message
from homeassistant.core import Event, HomeAssistant, callback

from ..const import DOMAIN
from ..core.area_manager import AreaManager
from ..core.coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


@websocket_command(
    {
        "type": "smart_heating/subscribe",
    }
)
@callback
def websocket_subscribe_updates(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe to area heater manager updates.

    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: Message data
    """
    _LOGGER.debug("WebSocket subscribe called")
    id_ = msg.get("id")
    if id_ is None:
        _LOGGER.debug("WebSocket subscribe called with missing id; ignoring")
        return

    # Find coordinator first
    coordinator = _find_coordinator(hass)
    if not coordinator:
        connection.send_error(id_, "not_loaded", "Smart Heating coordinator not found")
        return
    forward_cb = _create_forward_messages_callback(coordinator, connection, id_)

    # Subscribe to coordinator updates
    unsub = coordinator.async_add_listener(forward_cb)

    # Also subscribe to uninstall events and forward them to the client
    def _uninstall_event_listener(event: Event) -> None:
        try:
            connection.send_message(
                result_message(id_, {"event": "uninstall", "data": dict(event.data)})
            )
        except (RuntimeError, ConnectionError, TypeError) as err:
            _LOGGER.debug(
                "Failed to forward uninstall event to websocket client: %s", err, exc_info=True
            )

    bus_unsub = hass.bus.async_listen("smart_heating_uninstalled", _uninstall_event_listener)

    @callback
    def unsub_callback() -> None:
        """Unsubscribe from updates."""
        try:
            unsub()
        except (HomeAssistantError, SmartHeatingError, json.JSONDecodeError) as err:
            if isinstance(err, (KeyboardInterrupt, SystemExit)):
                raise
            _LOGGER.debug("Failed to unsubscribe from coordinator updates: %s", err, exc_info=True)
        try:
            bus_unsub()
        except (HomeAssistantError, SmartHeatingError, json.JSONDecodeError) as err:
            if isinstance(err, (KeyboardInterrupt, SystemExit)):
                raise
            _LOGGER.debug("Failed to unsubscribe from bus events: %s", err, exc_info=True)

    connection.subscriptions[msg["id"]] = unsub_callback
    connection.send_result(msg["id"])


@websocket_command(
    {
        "type": "smart_heating/get_areas",
    }
)
@callback
def websocket_get_areas(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all areas via websocket.

    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: Message data
    """
    id_ = msg.get("id")
    if id_ is None:
        _LOGGER.debug("WebSocket get_areas called with missing id; ignoring")
        return
    coordinator = _find_coordinator(hass)
    if not coordinator:
        connection.send_error(id_, "not_loaded", "Smart Heating not loaded")
        return
    area_manager = coordinator.area_manager

    areas_data = _get_all_areas_data(area_manager, hass)

    connection.send_result(msg["id"], {"areas": areas_data})


@websocket_command(
    {
        "type": "smart_heating/subscribe_device_logs",
        "area_id": str,
    }
)
@callback
def websocket_subscribe_device_logs(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe to live device logs for Smart Heating.

    Message may include optional `area_id` to filter events for a specific area.
    """
    _LOGGER.debug("WebSocket subscribe_device_logs called")
    id_ = msg.get("id")
    if id_ is None:
        _LOGGER.debug("WebSocket subscribe_device_logs called with missing id; ignoring")
        return

    coordinator = _find_coordinator(hass)
    if not coordinator:
        connection.send_error(id_, "not_loaded", "Smart Heating coordinator not found")
        return

    area_manager: AreaManager = coordinator.area_manager

    area_filter = msg.get("area_id")

    @callback
    def forward_event(event: dict[str, Any]) -> None:
        try:
            if area_filter and event.get("area_id") != area_filter:
                return
            connection.send_message(result_message(id_, {"event": "device_event", "data": event}))
        except (RuntimeError, ConnectionError, TypeError) as err:
            _LOGGER.debug(
                "Failed to forward device event to websocket client: %s", err, exc_info=True
            )

    # Register listener
    area_manager.add_device_log_listener(forward_event)

    @callback
    def unsub_callback() -> None:
        try:
            area_manager.remove_device_log_listener(forward_event)
        except (HomeAssistantError, SmartHeatingError, json.JSONDecodeError) as err:
            if isinstance(err, (KeyboardInterrupt, SystemExit)):
                raise
            _LOGGER.debug("Failed to remove device log listener: %s", err, exc_info=True)

    connection.subscriptions[msg["id"]] = unsub_callback
    connection.send_result(msg["id"])


def _get_all_areas_data(area_manager: AreaManager, hass: HomeAssistant) -> list[dict[str, Any]]:
    areas = area_manager.get_all_areas()
    areas_data = []
    for _area_id, area in areas.items():
        devices_data = []
        for dev_id, dev_data in area.devices.items():
            devices_data.append(_build_device_info(hass, dev_id, dev_data))
        areas_data.append(_build_area_summary(area, devices_data))
    return areas_data


def _create_forward_messages_callback(
    coordinator: SmartHeatingCoordinator, connection: ActiveConnection, id_: Any
) -> Callable[[], None]:
    @callback
    def forward_messages() -> None:
        area_count = len(coordinator.data.get("areas", {})) if coordinator.data else 0
        _LOGGER.debug("WebSocket: Sending update to client (areas: %d)", area_count)
        if coordinator.data and "areas" in coordinator.data:
            for area_id, area_data in coordinator.data["areas"].items():
                _LOGGER.debug(
                    "  Area %s: manual_override=%s, target_temp=%s",
                    area_id,
                    area_data.get("manual_override", "NOT SET"),
                    area_data.get("target_temperature"),
                )
        try:
            connection.send_message(
                result_message(id_, {"event": "update", "data": coordinator.data})
            )
        except (RuntimeError, ConnectionError, TypeError) as err:
            _LOGGER.debug("Failed to send update to websocket client: %s", err, exc_info=True)

    return forward_messages


def _find_coordinator(hass: HomeAssistant) -> SmartHeatingCoordinator | None:
    exclude_keys = {
        "history",
        "climate_controller",
        "schedule_executor",
        "learning_engine",
        "area_logger",
        "opentherm_logger",
        "vacation_manager",
        "safety_monitor",
        "climate_unsub",
        "user_manager",
        "efficiency_calculator",
        "comparison_engine",
        "config_manager",
    }
    # Use get to avoid KeyError if DOMAIN not present
    for key, value in hass.data.get(DOMAIN, {}).items():
        if key not in exclude_keys and hasattr(value, "async_add_listener"):
            return value
    return None


def _build_device_info(
    hass: HomeAssistant, dev_id: str, dev_data: dict[str, Any]
) -> dict[str, Any]:
    state = hass.states.get(dev_id)
    dev_type = dev_data.get("type")
    device_info = {
        "id": dev_id,
        "type": dev_type,
        "mqtt_topic": dev_data.get("mqtt_topic"),
        "state": state.state if state else "unavailable",
    }
    if state and state.attributes and dev_type:
        if dev_type == "thermostat":
            device_info["current_temperature"] = state.attributes.get("current_temperature")
            device_info["target_temperature"] = state.attributes.get("temperature")
            device_info["hvac_action"] = state.attributes.get("hvac_action")
            device_info["friendly_name"] = state.attributes.get("friendly_name", dev_id)
        elif dev_type == "temperature_sensor":
            device_info["temperature"] = state.attributes.get("temperature", state.state)
            device_info["friendly_name"] = state.attributes.get("friendly_name", dev_id)
        elif dev_type == "valve":
            device_info["position"] = state.attributes.get("position")
            device_info["friendly_name"] = state.attributes.get("friendly_name", dev_id)
    return device_info


def _build_area_summary(area: Any, devices_data: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": area.area_id,
        "name": area.name,
        "enabled": area.enabled,
        "state": area.state,
        "target_temperature": area.target_temperature,
        "current_temperature": area.current_temperature,
        "devices": devices_data,
        "schedules": [s.to_dict() for s in area.schedules.values()],
        # Night boost
        "night_boost_enabled": area.boost_manager.night_boost_enabled,
        "night_boost_offset": area.boost_manager.night_boost_offset,
        "night_boost_start_time": area.boost_manager.night_boost_start_time,
        "night_boost_end_time": area.boost_manager.night_boost_end_time,
        # Smart night boost
        "smart_boost_enabled": area.boost_manager.smart_boost_enabled,
        "smart_boost_target_time": area.boost_manager.smart_boost_target_time,
        "weather_entity_id": area.boost_manager.weather_entity_id,
        # Preset modes
        "preset_mode": area.preset_mode,
        "away_temp": area.away_temp,
        "eco_temp": area.eco_temp,
        "comfort_temp": area.comfort_temp,
        "home_temp": area.home_temp,
        "sleep_temp": area.sleep_temp,
        "activity_temp": area.activity_temp,
        # Boost mode
        "boost_mode_active": area.boost_manager.boost_mode_active,
        "boost_temp": area.boost_manager.boost_temp,
        "boost_duration": area.boost_manager.boost_duration,
        # HVAC mode
        "hvac_mode": area.hvac_mode,
        # Sensors
        "window_sensors": area.window_sensors,
        "presence_sensors": area.presence_sensors,
    }


async def setup_websocket(hass: HomeAssistant) -> None:
    """Set up WebSocket API.

    Args:
        hass: Home Assistant instance
    """
    async_register_command(hass, websocket_subscribe_updates)
    async_register_command(hass, websocket_get_areas)
    async_register_command(hass, websocket_subscribe_device_logs)

    # Ensure this function uses async features so linters don't suggest removing `async`
    await asyncio.sleep(0)

    _LOGGER.info("Smart Heating WebSocket API registered")
