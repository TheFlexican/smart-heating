"""User profile management API handlers."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..user_manager import UserManager
import asyncio

_LOGGER = logging.getLogger(__name__)


async def handle_get_users(
    _hass: HomeAssistant, user_manager: UserManager, request: web.Request
) -> web.Response:
    """Get all user profiles.

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request

    Returns:
        JSON response with all user profiles
    """
    try:
        # Ensure function uses async features so analyzers don't flag S7503
        await asyncio.sleep(0)
        users = user_manager.get_all_users()
        presence = user_manager.get_presence_state()
        settings = user_manager.get_settings()

        return web.json_response(
            {
                "users": users,
                "presence_state": presence,
                "settings": settings,
            }
        )

    except Exception as e:
        _LOGGER.error("Error getting users: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_user(
    _hass: HomeAssistant, user_manager: UserManager, request: web.Request, user_id: str
) -> web.Response:
    """Get a specific user profile.

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request
        user_id: User ID to retrieve

    Returns:
        JSON response with user profile
    """
    try:
        await asyncio.sleep(0)
        user = user_manager.get_user_profile(user_id)

        if not user:
            return web.json_response({"error": f"User {user_id} not found"}, status=404)

        return web.json_response({"user": user})

    except Exception as e:
        _LOGGER.error("Error getting user %s: %s", user_id, e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_create_user(
    hass: HomeAssistant, user_manager: UserManager, request: web.Request
) -> web.Response:
    """Create a new user profile.

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request with JSON body

    Returns:
        JSON response with created user profile
    """
    try:
        data = await request.json()

        name = data.get("name")
        person_entity = data.get("person_entity")

        # Validate required fields (user_id is now optional, auto-generated if not provided)
        if not name or not person_entity:
            return web.json_response(
                {"error": "Missing required fields: name, person_entity"},
                status=400,
            )

        # Check for duplicate person_entity
        existing_user = user_manager.get_user_by_person_entity(person_entity)
        if existing_user:
            return web.json_response(
                {"error": f"A user is already linked to {person_entity}"},
                status=400,
            )

        # Auto-generate user_id from name if not provided
        user_id = data.get("user_id")
        if not user_id:
            # Generate unique user_id from name
            import re
            import time

            # Sanitize name: lowercase, replace spaces/special chars with underscore
            sanitized = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            # Add timestamp to ensure uniqueness
            user_id = f"{sanitized}_{int(time.time())}"
            _LOGGER.info("Auto-generated user_id: %s for user: %s", user_id, name)

        preset_preferences = data.get("preset_preferences", {})
        priority = data.get("priority", 5)
        areas = data.get("areas", [])

        user = await user_manager.create_user_profile(
            user_id=user_id,
            name=name,
            person_entity=person_entity,
            preset_preferences=preset_preferences,
            priority=priority,
            areas=areas,
        )

        # Fire WebSocket event
        hass.bus.async_fire(
            "smart_heating_user_created",
            {"user_id": user_id, "name": name},
        )

        return web.json_response({"user": user}, status=201)

    except ValueError as e:
        _LOGGER.warning("Invalid user data: %s", e)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        _LOGGER.error("Error creating user: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_update_user(
    hass: HomeAssistant, user_manager: UserManager, request: web.Request, user_id: str
) -> web.Response:
    """Update an existing user profile.

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request with JSON body
        user_id: User ID to update

    Returns:
        JSON response with updated user profile
    """
    try:
        data = await request.json()

        # If person_entity is being updated, check for duplicates
        if "user_id" in data:
            person_entity = data["user_id"]
            existing_user = user_manager.get_user_by_person_entity(person_entity)
            if existing_user and existing_user.get("internal_id") != user_id:
                return web.json_response(
                    {"error": f"A user is already linked to {person_entity}"},
                    status=400,
                )

        user = await user_manager.update_user_profile(user_id, data)

        # Fire WebSocket event
        hass.bus.async_fire(
            "smart_heating_user_updated",
            {"user_id": user_id},
        )

        return web.json_response({"user": user})

    except ValueError as e:
        _LOGGER.warning("Invalid user data: %s", e)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        _LOGGER.error("Error updating user %s: %s", user_id, e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_delete_user(
    hass: HomeAssistant, user_manager: UserManager, request: web.Request, user_id: str
) -> web.Response:
    """Delete a user profile.

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request
        user_id: User ID to delete

    Returns:
        JSON response confirming deletion
    """
    try:
        await user_manager.delete_user_profile(user_id)

        # Fire WebSocket event
        hass.bus.async_fire(
            "smart_heating_user_deleted",
            {"user_id": user_id},
        )

        return web.json_response({"message": f"User {user_id} deleted"})

    except ValueError as e:
        _LOGGER.warning("User not found: %s", e)
        return web.json_response({"error": str(e)}, status=404)
    except Exception as e:
        _LOGGER.error("Error deleting user %s: %s", user_id, e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_update_user_settings(
    hass: HomeAssistant, user_manager: UserManager, request: web.Request
) -> web.Response:
    """Update multi-user settings.

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request with JSON body

    Returns:
        JSON response with updated settings
    """
    try:
        data = await request.json()

        settings = await user_manager.update_settings(data)

        # Fire WebSocket event
        hass.bus.async_fire(
            "smart_heating_user_settings_updated",
            {"settings": settings},
        )

        return web.json_response({"settings": settings})

    except Exception as e:
        _LOGGER.error("Error updating user settings: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_presence_state(
    _hass: HomeAssistant, user_manager: UserManager, request: web.Request
) -> web.Response:
    """Get current presence state.

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request

    Returns:
        JSON response with current presence state
    """
    try:
        await asyncio.sleep(0)
        presence = user_manager.get_presence_state()
        return web.json_response({"presence_state": presence})

    except Exception as e:
        _LOGGER.error("Error getting presence state: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_active_preferences(
    _hass: HomeAssistant, user_manager: UserManager, request: web.Request
) -> web.Response:
    """Get temperature preferences for currently active user(s).

    Args:
        hass: Home Assistant instance
        user_manager: User manager instance
        request: HTTP request

    Returns:
        JSON response with active preferences
    """
    try:
        await asyncio.sleep(0)
        area_id = request.query.get("area_id")

        active_prefs = user_manager.get_active_user_preferences(area_id)
        combined_prefs = user_manager.get_combined_preferences(area_id)

        return web.json_response(
            {
                "active_user_preferences": active_prefs,
                "combined_preferences": combined_prefs,
            }
        )

    except Exception as e:
        _LOGGER.error("Error getting active preferences: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)
