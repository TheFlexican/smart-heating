from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp.test_utils import make_mocked_request
from smart_heating.api_handlers import users as users_mod


@pytest.mark.asyncio
async def test_handle_get_users():
    hass = MagicMock()
    um = MagicMock()
    um.get_all_users.return_value = {"u1": {}}
    um.get_presence_state.return_value = {"home": True}
    um.get_settings.return_value = {"multi_user": True}

    req = make_mocked_request("GET", "/api/users")
    resp = await users_mod.handle_get_users(hass, um, req)
    assert resp.status == 200
    import json as _json

    data = _json.loads(resp.body.decode())
    assert "users" in data


@pytest.mark.asyncio
async def test_handle_get_user_not_found():
    hass = MagicMock()
    um = MagicMock()
    um.get_user_profile.return_value = None
    req = make_mocked_request("GET", "/api/users/u1")
    resp = await users_mod.handle_get_user(hass, um, req, "u1")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_handle_get_user_success():
    hass = MagicMock()
    um = MagicMock()
    um.get_user_profile.return_value = {"name": "Ralf"}
    req = make_mocked_request("GET", "/api/users/u1")
    resp = await users_mod.handle_get_user(hass, um, req, "u1")
    assert resp.status == 200
    import json as _json

    data = _json.loads(resp.body.decode())
    assert "user" in data


@pytest.mark.asyncio
async def test_handle_create_user_validation_and_success():
    hass = MagicMock()
    um = MagicMock()
    # missing fields
    req = make_mocked_request("POST", "/api/users")
    req.json = AsyncMock(return_value={})
    resp = await users_mod.handle_create_user(hass, um, req)
    assert resp.status == 400

    # success
    req.json = AsyncMock(return_value={"user_id": "u1", "name": "R", "person_entity": "person.r"})
    um.create_user_profile = AsyncMock(return_value={"user_id": "u1"})
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    resp = await users_mod.handle_create_user(hass, um, req)
    assert resp.status == 201
    import json as _json

    data = _json.loads(resp.body.decode())
    assert "user" in data


@pytest.mark.asyncio
async def test_handle_update_user_and_value_error():
    hass = MagicMock()
    um = MagicMock()
    req = make_mocked_request("PUT", "/api/users/u1")
    req.json = AsyncMock(return_value={"name": "New"})
    um.update_user_profile = AsyncMock(return_value={"user_id": "u1"})
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    resp = await users_mod.handle_update_user(hass, um, req, "u1")
    assert resp.status == 200

    # ValueError path
    um.update_user_profile = AsyncMock(side_effect=ValueError("bad"))
    resp = await users_mod.handle_update_user(hass, um, req, "u1")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_handle_delete_user_and_not_found():
    hass = MagicMock()
    um = MagicMock()
    um.delete_user_profile = AsyncMock(return_value=None)
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    resp = await users_mod.handle_delete_user(hass, um, None, "u1")
    assert resp.status == 200

    # not found
    um.delete_user_profile = AsyncMock(side_effect=ValueError("missing"))
    resp = await users_mod.handle_delete_user(hass, um, None, "u1")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_handle_update_user_settings_and_presence_and_active_prefs():
    hass = MagicMock()
    um = MagicMock()
    # settings update
    req = make_mocked_request("POST", "/api/users/settings")
    req.json = AsyncMock(return_value={"multi_user": True})
    um.update_settings = AsyncMock(return_value={"multi_user": True})
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    resp = await users_mod.handle_update_user_settings(hass, um, req)
    assert resp.status == 200

    # presence
    req = make_mocked_request("GET", "/api/users/presence")
    um.get_presence_state.return_value = {"home": True}
    resp = await users_mod.handle_get_presence_state(hass, um, req)
    assert resp.status == 200

    # active prefs
    req = make_mocked_request("GET", "/api/users/active_prefs?area_id=a1")
    um.get_active_user_preferences.return_value = {"a1": {}}
    um.get_combined_preferences.return_value = {"a1": {}}
    resp = await users_mod.handle_get_active_preferences(hass, um, req)
    assert resp.status == 200
