"""Config flow for Gree Cloud integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .greeclimate.cloud_api import GreeCloudApi, GREE_CLOUD_SERVERS as API_SERVERS

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_REGION,
    DEFAULT_REGION,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    region = data.get(CONF_REGION, DEFAULT_REGION)

    try:
        api = GreeCloudApi.for_server(region, username, password)
        credentials = await api.login()
        await api.close()
    except Exception as exc:
        raise InvalidAuth from exc

    return {
        "title": f"Gree Cloud ({username})",
        "username": username,
        "password": password,
        "region": region,
        "user_id": credentials.user_id,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gree Cloud."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._username: str | None = None
        self._password: str | None = None
        self._region: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(str(info.get("user_id", info[CONF_USERNAME])))
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        # Show form with username, password, and region selection
        # Using Europe as default region as per requirements
        step_user_data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(list(API_SERVERS.keys())),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=step_user_data_schema, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Gree Cloud."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init")


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
