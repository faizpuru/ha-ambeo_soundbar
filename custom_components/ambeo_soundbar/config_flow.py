import logging
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_PORT
from .api.factory import AmbeoAPIFactory
from homeassistant.exceptions import ConfigEntryError

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass, host, port=DEFAULT_PORT):
    """Validate connection to Ambeo device and return name if successful."""
    async with aiohttp.ClientSession() as client_session:
        try:
            ambeo_api = await AmbeoAPIFactory.create_api(
                host, port, client_session, hass)
            name = await ambeo_api.get_name()
            return name, None
        except Exception as error:
            _LOGGER.error("Connection error to %s: %s", host, error)
            return None, "cannot_connect"


class AmbeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options configuration for Ambeo Soundbar integration."""

    async def async_step_init(self, user_input=None):
        errors = {}
        host_default = self.config_entry.options.get(
            "host", self.config_entry.data.get("host"))
        if user_input is not None:
            name, error = await validate_connection(self.hass, user_input["host"])
            if error is not None:
                errors["base"] = error
                return self.display_form(errors, host_default)
            else:
                return self.async_create_entry(data=user_input)

        return self.display_form(errors, host_default)

    def display_form(self, errors, host_default):
        options_schema = vol.Schema({
            vol.Optional("host", default=host_default): str,
            vol.Optional("experimental", default=self.config_entry.options.get("experimental", False)): bool,
            vol.Optional("cooldown", default=self.config_entry.options.get("cooldown", 90)): int,
        })
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors
        )


class AmbeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Manage the configuration flow for Ambeo Soundbar integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a configuration initiated by the user."""
        errors = {}

        if user_input is not None:
            host = user_input.get("host")
            name, error = await validate_connection(self.hass, host)

            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(title=name, data=user_input)

        data_schema = vol.Schema({
            vol.Required("host", default="ambeo.local"): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return AmbeoOptionsFlowHandler()
