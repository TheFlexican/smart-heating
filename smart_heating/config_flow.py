"""Config flow for Smart Heating integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartHeatingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Heating."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step.

        This is a simple config flow that doesn't require any user input.

        Args:
            user_input: User input data (not used in this basic implementation)

        Returns:
            FlowResult: Result of the flow step
        """
        _LOGGER.debug("Config flow started")

        # Check if already configured - only abort if there's an active entry
        existing_entries = self._async_current_entries()
        if existing_entries:
            _LOGGER.debug("Found %d existing entries", len(existing_entries))
            # Check if any entry is not being removed
            active_entries = [
                e
                for e in existing_entries
                if e.state
                not in (
                    config_entries.ConfigEntryState.NOT_LOADED,
                    config_entries.ConfigEntryState.FAILED_UNLOAD,
                )
            ]
            if active_entries:
                _LOGGER.debug("Smart Heating already configured with active entry")
                return self.async_abort(reason="already_configured")
            else:
                _LOGGER.debug("Found entries but none are active, allowing new setup")

        if user_input is not None:
            _LOGGER.debug("Creating config entry")
            # Create the config entry
            return self.async_create_entry(
                title="Smart Heating",
                data={},
            )

        # Show the configuration form (empty in this case)
        _LOGGER.debug("Showing config form")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler.

        Args:
            config_entry: Config entry instance

        Returns:
            OptionsFlow: Options flow handler
        """
        return SmartHeatingOptionsFlowHandler()


class SmartHeatingOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Smart Heating."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options.

        All configuration is now done via Global Settings in the Smart Heating UI.
        This options flow is kept minimal to avoid configuration conflicts.

        Args:
            user_input: User input data

        Returns:
            FlowResult: Result of the flow step
        """
        if user_input is not None:
            return self.async_create_entry(title="", data={})

        # Offer an option to select an OpenTherm Gateway if present in Home Assistant
        gw_entries = self.hass.config_entries.async_entries(domain="opentherm_gw")
        if gw_entries:
            gateway_ids = [entry.data.get("id") for entry in gw_entries if entry.data.get("id")]
            schema = vol.Schema({"opentherm_gateway_id": vol.In([""] + gateway_ids)})
        else:
            schema = vol.Schema({})

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "info": "All Smart Heating configuration is managed via Global Settings in the Smart Heating panel. "
                "Click the gear icon in the Smart Heating UI to access Global Settings."
            },
        )
