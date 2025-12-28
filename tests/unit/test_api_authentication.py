"""Test authentication and authorization for Smart Heating API."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from smart_heating.api.server import SmartHeatingAPIView
from smart_heating.const import DOMAIN


@pytest.fixture
def admin_user():
    """Create a mock admin user."""
    user = MagicMock()
    user.is_admin = True
    user.id = "admin-user-id"
    user.name = "Admin User"
    return user


@pytest.fixture
def regular_user():
    """Create a mock regular (non-admin) user."""
    user = MagicMock()
    user.is_admin = False
    user.id = "regular-user-id"
    user.name = "Regular User"
    return user


@pytest.fixture
def api_view_with_mocks(hass, mock_area_manager):
    """Create API view with all required mocks."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config_manager"] = MagicMock()
    hass.data[DOMAIN]["user_manager"] = MagicMock()
    hass.data[DOMAIN]["efficiency_calculator"] = MagicMock()
    hass.data[DOMAIN]["comparison_engine"] = MagicMock()

    return SmartHeatingAPIView(hass, mock_area_manager)


class TestAuthenticationRequired:
    """Test that authentication is required."""

    def test_view_requires_auth(self):
        """Test that the view has requires_auth set to True."""
        assert SmartHeatingAPIView.requires_auth is True


class TestGetOperationsAuthentication:
    """Test GET operations only require authentication, not admin."""

    @pytest.mark.asyncio
    async def test_get_status_with_regular_user(
        self, api_view_with_mocks, regular_user, mock_area_manager
    ):
        """Test regular user can access GET endpoints."""
        with patch(
            "smart_heating.api.server.handle_get_status",
            AsyncMock(return_value=web.json_response({"status": "ok"})),
        ):
            req = make_mocked_request("GET", "/api/smart_heating/status")
            req["hass_user"] = regular_user

            resp = await api_view_with_mocks.get(req, "status")
            assert resp.status == 200

    @pytest.mark.asyncio
    async def test_get_areas_with_regular_user(
        self, api_view_with_mocks, regular_user, mock_area_manager
    ):
        """Test regular user can list areas."""
        with patch(
            "smart_heating.api.server.handle_get_areas",
            AsyncMock(return_value=web.json_response({"areas": []})),
        ):
            req = make_mocked_request("GET", "/api/smart_heating/areas")
            req["hass_user"] = regular_user

            resp = await api_view_with_mocks.get(req, "areas")
            assert resp.status == 200


class TestPostOperationsRequireAdmin:
    """Test POST operations require admin permission."""

    @pytest.mark.asyncio
    async def test_post_without_user_returns_401(self, api_view_with_mocks):
        """Test POST without user returns 401 Unauthorized."""
        req = make_mocked_request("POST", "/api/smart_heating/areas")
        # No hass_user in request

        resp = await api_view_with_mocks.post(req, "areas")
        assert resp.status == 401
        # Verify error message in response body
        assert "Authentication required" in resp.text

    @pytest.mark.asyncio
    async def test_post_with_regular_user_returns_403(self, api_view_with_mocks, regular_user):
        """Test POST with non-admin user returns 403 Forbidden."""
        req = make_mocked_request("POST", "/api/smart_heating/areas")
        req["hass_user"] = regular_user

        resp = await api_view_with_mocks.post(req, "areas")
        assert resp.status == 403
        # Verify error message in response body
        assert "Admin permission required" in resp.text

    @pytest.mark.asyncio
    async def test_post_with_admin_user_succeeds(
        self, api_view_with_mocks, admin_user, mock_area_manager
    ):
        """Test POST with admin user succeeds."""
        with patch(
            "smart_heating.api.server.handle_enable_area",
            AsyncMock(return_value=web.json_response({"success": True})),
        ):
            req = make_mocked_request("POST", "/api/smart_heating/areas/test_area/enable")
            req["hass_user"] = admin_user

            resp = await api_view_with_mocks.post(req, "areas/test_area/enable")
            assert resp.status == 200

    @pytest.mark.asyncio
    async def test_post_area_temperature_requires_admin(
        self, api_view_with_mocks, regular_user, admin_user
    ):
        """Test setting temperature requires admin."""
        # Regular user - should fail
        req = make_mocked_request("POST", "/api/smart_heating/areas/test/temperature")
        req["hass_user"] = regular_user

        resp = await api_view_with_mocks.post(req, "areas/test/temperature")
        assert resp.status == 403

        # Admin user - should succeed
        with patch(
            "smart_heating.api.server.handle_set_temperature",
            AsyncMock(return_value=web.json_response({"success": True})),
        ):
            req = make_mocked_request("POST", "/api/smart_heating/areas/test/temperature")
            req["hass_user"] = admin_user
            req._read_bytes = b'{"temperature": 20}'

            resp = await api_view_with_mocks.post(req, "areas/test/temperature")
            assert resp.status == 200


class TestPatchOperationsRequireAdmin:
    """Test PATCH operations require admin permission."""

    @pytest.mark.asyncio
    async def test_patch_without_user_returns_401(self, api_view_with_mocks):
        """Test PATCH without user returns 401 Unauthorized."""
        req = make_mocked_request("PATCH", "/api/smart_heating/areas/test/schedules/1")
        # No hass_user in request

        resp = await api_view_with_mocks.patch(req, "areas/test/schedules/1")
        assert resp.status == 401

    @pytest.mark.asyncio
    async def test_patch_with_regular_user_returns_403(self, api_view_with_mocks, regular_user):
        """Test PATCH with non-admin user returns 403 Forbidden."""
        req = make_mocked_request("PATCH", "/api/smart_heating/areas/test/schedules/1")
        req["hass_user"] = regular_user

        resp = await api_view_with_mocks.patch(req, "areas/test/schedules/1")
        assert resp.status == 403

    @pytest.mark.asyncio
    async def test_patch_with_admin_user_succeeds(self, api_view_with_mocks, admin_user):
        """Test PATCH with admin user succeeds."""
        with patch(
            "smart_heating.api.server.handle_update_schedule",
            AsyncMock(return_value=web.json_response({"success": True})),
        ):
            req = make_mocked_request("PATCH", "/api/smart_heating/areas/test/schedules/1")
            req["hass_user"] = admin_user
            req._read_bytes = b'{"enabled": true}'

            resp = await api_view_with_mocks.patch(req, "areas/test/schedules/1")
            assert resp.status == 200


class TestDeleteOperationsRequireAdmin:
    """Test DELETE operations require admin permission."""

    @pytest.mark.asyncio
    async def test_delete_without_user_returns_401(self, api_view_with_mocks):
        """Test DELETE without user returns 401 Unauthorized."""
        req = make_mocked_request("DELETE", "/api/smart_heating/vacation_mode")
        # No hass_user in request

        resp = await api_view_with_mocks.delete(req, "vacation_mode")
        assert resp.status == 401

    @pytest.mark.asyncio
    async def test_delete_with_regular_user_returns_403(self, api_view_with_mocks, regular_user):
        """Test DELETE with non-admin user returns 403 Forbidden."""
        req = make_mocked_request("DELETE", "/api/smart_heating/vacation_mode")
        req["hass_user"] = regular_user

        resp = await api_view_with_mocks.delete(req, "vacation_mode")
        assert resp.status == 403

    @pytest.mark.asyncio
    async def test_delete_with_admin_user_succeeds(self, api_view_with_mocks, admin_user):
        """Test DELETE with admin user succeeds."""
        with patch(
            "smart_heating.api.server.handle_disable_vacation_mode",
            AsyncMock(return_value=web.json_response({"success": True})),
        ):
            req = make_mocked_request("DELETE", "/api/smart_heating/vacation_mode")
            req["hass_user"] = admin_user

            resp = await api_view_with_mocks.delete(req, "vacation_mode")
            assert resp.status == 200

    @pytest.mark.asyncio
    async def test_delete_area_device_requires_admin(
        self, api_view_with_mocks, regular_user, admin_user
    ):
        """Test deleting area device requires admin."""
        # Regular user - should fail
        req = make_mocked_request("DELETE", "/api/smart_heating/areas/test/devices/dev1")
        req["hass_user"] = regular_user

        resp = await api_view_with_mocks.delete(req, "areas/test/devices/dev1")
        assert resp.status == 403

        # Admin user - should succeed
        with patch(
            "smart_heating.api.server.handle_remove_device",
            AsyncMock(return_value=web.json_response({"success": True})),
        ):
            req = make_mocked_request("DELETE", "/api/smart_heating/areas/test/devices/dev1")
            req["hass_user"] = admin_user

            resp = await api_view_with_mocks.delete(req, "areas/test/devices/dev1")
            assert resp.status == 200


class TestAuthHelpers:
    """Test authentication helper functions."""

    def test_require_admin_with_no_user(self):
        """Test require_admin returns 401 for no user."""
        from smart_heating.api.auth import require_admin

        result = require_admin(None)
        assert result is not None
        assert result.status == 401

    def test_require_admin_with_regular_user(self, regular_user):
        """Test require_admin returns 403 for non-admin user."""
        from smart_heating.api.auth import require_admin

        result = require_admin(regular_user)
        assert result is not None
        assert result.status == 403

    def test_require_admin_with_admin_user(self, admin_user):
        """Test require_admin returns None for admin user."""
        from smart_heating.api.auth import require_admin

        result = require_admin(admin_user)
        assert result is None

    def test_get_user_from_request(self, admin_user):
        """Test extracting user from request."""
        from smart_heating.api.auth import get_user_from_request

        req = make_mocked_request("GET", "/test")
        req["hass_user"] = admin_user

        user = get_user_from_request(req)
        assert user == admin_user

    def test_get_user_from_request_no_user(self):
        """Test extracting user from request with no user."""
        from smart_heating.api.auth import get_user_from_request

        req = make_mocked_request("GET", "/test")

        user = get_user_from_request(req)
        assert user is None
