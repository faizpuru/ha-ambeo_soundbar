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

    def __init__(self, config_entry):
        """Initialize options handler with existing configuration."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        errors = {}

        if user_input is not None:
            if "host" in user_input and user_input["host"] != self.config_entry.data.get("host"):
                name, error = await validate_connection(self.hass, user_input["host"])

                if error:
                    errors["base"] = error
                else:
                    # Update configuration with new host
                    new_data = dict(self.config_entry.data)
                    new_data["host"] = user_input["host"]

                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data=new_data,
                        title=name
                    )

                    # Reload entry to apply changes
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(
                            self.config_entry.entry_id)
                    )

                    return self.async_create_entry(title="", data={})
            else:
                return self.async_create_entry(title="", data=user_input)

        host_default = self.config_entry.data.get("host")
        options_schema = vol.Schema({
            vol.Optional("host", default=host_default): str,
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
        return AmbeoOptionsFlowHandler(config_entry)
