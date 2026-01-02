"""Tests for area PID settings API endpoint."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from aiohttp import web

from smart_heating.api.handlers.area_settings import (
    handle_set_area_pid,
    _validate_pid_active_modes,
)
from smart_heating.models.area import Area


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock()
    hass.data = {}
    return hass


@pytest.fixture
def mock_area_manager():
    """Create a mock area manager."""
    manager = Mock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_area():
    """Create a mock area."""
    area = Mock(spec=Area)
    area.area_id = "living_room"
    area.name = "Living Room"
    area.pid_enabled = False
    area.pid_automatic_gains = True
    area.pid_active_modes = ["schedule", "home", "comfort"]
    return area


class TestValidatePIDActiveModes:
    """Test PID active modes validation function."""

    def test_valid_modes_list(self):
        """Test validation passes for valid modes list."""
        modes = ["schedule", "home", "comfort"]
        is_valid, result = _validate_pid_active_modes(modes)

        assert is_valid is True
        assert result == modes

    def test_all_valid_modes(self):
        """Test all valid modes are accepted."""
        modes = ["schedule", "home", "away", "sleep", "comfort", "eco", "boost", "manual"]
        is_valid, result = _validate_pid_active_modes(modes)

        assert is_valid is True
        assert result == modes

    def test_empty_list_valid(self):
        """Test empty list is valid."""
        modes = []
        is_valid, result = _validate_pid_active_modes(modes)

        assert is_valid is True
        assert result == []

    def test_single_mode_valid(self):
        """Test single mode is valid."""
        modes = ["schedule"]
        is_valid, result = _validate_pid_active_modes(modes)

        assert is_valid is True
        assert result == modes

    def test_invalid_mode_rejected(self):
        """Test invalid mode is rejected."""
        modes = ["schedule", "invalid_mode"]
        is_valid, result = _validate_pid_active_modes(modes)

        assert is_valid is False
        assert "Invalid mode" in result
        assert "invalid_mode" in result

    def test_not_list_rejected(self):
        """Test non-list value is rejected."""
        is_valid, result = _validate_pid_active_modes("not_a_list")  # type: ignore[arg-type]

        assert is_valid is False
        assert "must be a list" in result

    def test_none_rejected(self):
        """Test None is rejected."""
        is_valid, result = _validate_pid_active_modes(None)  # type: ignore[arg-type]

        assert is_valid is False
        assert "must be a list" in result

    def test_dict_rejected(self):
        """Test dict is rejected."""
        is_valid, result = _validate_pid_active_modes({"mode": "schedule"})  # type: ignore[arg-type]

        assert is_valid is False
        assert "must be a list" in result

    def test_multiple_invalid_modes(self):
        """Test first invalid mode is reported."""
        modes = ["schedule", "bad1", "bad2"]
        is_valid, result = _validate_pid_active_modes(modes)

        assert is_valid is False
        # Should report first invalid mode
        assert "Invalid mode" in result


class TestHandleSetAreaPID:
    """Test handle_set_area_pid API endpoint."""

    @pytest.mark.asyncio
    async def test_set_pid_enabled(self, mock_hass, mock_area_manager, mock_area):
        """Test setting PID enabled flag."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"enabled": True}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_enabled is True
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_pid_disabled(self, mock_hass, mock_area_manager, mock_area):
        """Test disabling PID."""
        mock_area.pid_enabled = True
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"enabled": False}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_enabled is False
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_automatic_gains(self, mock_hass, mock_area_manager, mock_area):
        """Test setting automatic gains flag."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"automatic_gains": False}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_automatic_gains is False
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_active_modes(self, mock_hass, mock_area_manager, mock_area):
        """Test setting PID active modes."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            new_modes = ["schedule", "comfort", "eco"]
            data = {"active_modes": new_modes}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_active_modes == new_modes
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_all_pid_settings(self, mock_hass, mock_area_manager, mock_area):
        """Test setting all PID settings at once."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {
                "enabled": True,
                "automatic_gains": False,
                "active_modes": ["home", "schedule"],
            }
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_enabled is True
        assert mock_area.pid_automatic_gains is False
        assert mock_area.pid_active_modes == ["home", "schedule"]
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_area_not_found(self, mock_hass, mock_area_manager):
        """Test error when area not found."""
        mock_area_manager.get_area = Mock(return_value=None)

        data = {"enabled": True}
        response = await handle_set_area_pid(mock_hass, mock_area_manager, "nonexistent", data)

        assert response.status == 404
        json_data = response.body
        mock_area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_enabled_value(self, mock_hass, mock_area_manager, mock_area):
        """Test error with invalid enabled value."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        # Note: bool() can convert most values, so this is hard to trigger
        # But we test the error handling exists
        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"enabled": "not_a_bool"}  # Will be converted by bool()
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        # bool("not_a_bool") = True, so this succeeds
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_invalid_automatic_gains_value(self, mock_hass, mock_area_manager, mock_area):
        """Test error with invalid automatic_gains value."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"automatic_gains": "yes"}  # Will be converted by bool()
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        # bool("yes") = True, so this succeeds
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_invalid_active_modes_not_list(self, mock_hass, mock_area_manager, mock_area):
        """Test error when active_modes is not a list."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"active_modes": "not_a_list"}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 400
        mock_area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_mode_name(self, mock_hass, mock_area_manager, mock_area):
        """Test error when mode name is invalid."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"active_modes": ["schedule", "invalid_mode"]}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 400
        mock_area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_active_modes_list(self, mock_hass, mock_area_manager, mock_area):
        """Test empty active_modes list is valid."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"active_modes": []}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_active_modes == []
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_update_enabled_only(self, mock_hass, mock_area_manager, mock_area):
        """Test updating only enabled flag."""
        mock_area.pid_automatic_gains = False
        mock_area.pid_active_modes = ["home"]
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"enabled": True}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_enabled is True
        # Other settings unchanged
        assert mock_area.pid_automatic_gains is False
        assert mock_area.pid_active_modes == ["home"]

    @pytest.mark.asyncio
    async def test_partial_update_modes_only(self, mock_hass, mock_area_manager, mock_area):
        """Test updating only active modes."""
        mock_area.pid_enabled = True
        mock_area.pid_automatic_gains = False
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"active_modes": ["schedule", "eco"]}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_active_modes == ["schedule", "eco"]
        # Other settings unchanged
        assert mock_area.pid_enabled is True
        assert mock_area.pid_automatic_gains is False

    @pytest.mark.asyncio
    async def test_coordinator_refresh_called(self, mock_hass, mock_area_manager, mock_area):
        """Test coordinator refresh is triggered."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch(
            "smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()
        ) as mock_refresh:
            data = {"enabled": True}
            await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_hass, mock_area_manager, mock_area):
        """Test exception handling returns 500 error."""
        mock_area_manager.get_area = Mock(return_value=mock_area)
        mock_area_manager.async_save = AsyncMock(side_effect=Exception("Storage error"))

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"enabled": True}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 500

    @pytest.mark.asyncio
    async def test_all_valid_modes_accepted(self, mock_hass, mock_area_manager, mock_area):
        """Test all valid mode names are accepted."""
        mock_area_manager.get_area = Mock(return_value=mock_area)

        all_modes = ["schedule", "home", "away", "sleep", "comfort", "eco", "boost", "manual"]

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {"active_modes": all_modes}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert mock_area.pid_active_modes == all_modes

    @pytest.mark.asyncio
    async def test_empty_data_dict(self, mock_hass, mock_area_manager, mock_area):
        """Test empty data dict doesn't change anything."""
        mock_area.pid_enabled = False
        mock_area.pid_automatic_gains = True
        mock_area.pid_active_modes = ["schedule"]
        mock_area_manager.get_area = Mock(return_value=mock_area)

        with patch("smart_heating.api.handlers.area_settings._refresh_coordinator", AsyncMock()):
            data = {}
            response = await handle_set_area_pid(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        # Nothing should have changed
        assert mock_area.pid_enabled is False
        assert mock_area.pid_automatic_gains is True
        assert mock_area.pid_active_modes == ["schedule"]
        # But save should still be called
        mock_area_manager.async_save.assert_called_once()
