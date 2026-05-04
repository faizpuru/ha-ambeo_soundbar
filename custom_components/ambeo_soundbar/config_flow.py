"""Config flow for Ambeo Soundbar integration."""

import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api.exceptions import AmbeoConnectionError
from .api.factory import AmbeoAPIFactory
from .const import (
    CONFIG_CONCURRENT_REQUESTS,
    CONFIG_CONCURRENT_REQUESTS_DEFAULT,
    CONFIG_HOST,
    CONFIG_HOST_DEFAULT,
    CONFIG_UPDATE_INTERVAL,
    CONFIG_UPDATE_INTERVAL_DEFAULT,
    DEFAULT_PORT,
    DOMAIN,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(
    hass: HomeAssistant, host: str, port: int = DEFAULT_PORT
) -> tuple[str | None, str | None, str | None]:
    """Validate connection to Ambeo device and return name if successful."""
    client_session = async_create_clientsession(hass)
    try:
        ambeo_api = await AmbeoAPIFactory.create_api(
            host, port, TIMEOUT, client_session
        )
        name = await ambeo_api.get_name()
        serial = await ambeo_api.get_serial()
        return name, serial, None
    except (AmbeoConnectionError, aiohttp.ClientError) as error:
        _LOGGER.error("Connection error to %s: %s", host, error)
        return None, None, "cannot_connect"


class AmbeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options configuration for Ambeo Soundbar integration."""

    async def async_step_init(self, user_input=None):
        """Handle the initial step of the options flow."""
        errors = {}
        host_default = self.config_entry.options.get(
            CONFIG_HOST, self.config_entry.data.get(CONFIG_HOST)
        )
        if user_input is not None:
            name, serial, error = await validate_connection(
                self.hass, user_input[CONFIG_HOST]
            )
            if error is not None:
                errors["base"] = error
                return self.display_form(errors, host_default)
            else:
                return self.async_create_entry(data=user_input)

        return self.display_form(errors, host_default)

    def display_form(self, errors, host_default):
        """Build and display the options form."""
        update_interval_default = self.config_entry.options.get(
            CONFIG_UPDATE_INTERVAL, CONFIG_UPDATE_INTERVAL_DEFAULT
        )

        schema: dict = {
            vol.Optional(CONFIG_HOST, default=host_default): str,
            vol.Optional(CONFIG_UPDATE_INTERVAL, default=update_interval_default): int,
            vol.Optional(
                CONFIG_CONCURRENT_REQUESTS,
                default=self.config_entry.options.get(
                    CONFIG_CONCURRENT_REQUESTS, CONFIG_CONCURRENT_REQUESTS_DEFAULT
                ),
            ): int,
        }

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema), errors=errors
        )


class AmbeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Manage the configuration flow for Ambeo Soundbar integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a configuration initiated by the user."""
        errors = {}

        if user_input is not None:
            host = user_input.get(CONFIG_HOST)
            name, serial, error = await validate_connection(self.hass, host)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name or "Ambeo Soundbar", data=user_input
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONFIG_HOST, default=CONFIG_HOST_DEFAULT): str,
                vol.Optional(
                    CONFIG_UPDATE_INTERVAL, default=CONFIG_UPDATE_INTERVAL_DEFAULT
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return AmbeoOptionsFlowHandler()
