"""Authentication helpers for Smart Heating API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from homeassistant.auth.models import User


def require_admin(user: User | None) -> web.Response | None:
    """Check if user is admin.

    Args:
        user: User from request context

    Returns:
        Error response if not admin, None if admin
    """
    if not user:
        return web.json_response({"error": "Authentication required"}, status=401)

    if not user.is_admin:
        return web.json_response({"error": "Admin permission required"}, status=403)

    return None


def get_user_from_request(request: web.Request) -> User | None:
    """Extract user from request.

    Args:
        request: aiohttp request

    Returns:
        User object or None
    """
    return request.get("hass_user")
