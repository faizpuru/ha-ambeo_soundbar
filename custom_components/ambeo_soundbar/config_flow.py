import logging
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from .const import CONFIG_DEBOUNCE_COOLDOWN_DEFAULT, CONFIG_HOST_DEFAULT, DOMAIN, DEFAULT_PORT, CONFIG_HOST, CONFIG_DEBOUNCE_COOLDOWN
from .api.factory import AmbeoAPIFactory

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass, host, port=DEFAULT_PORT):
    """Validate connection to Ambeo device and return name if successful."""
    async with aiohttp.ClientSession() as client_session:
        try:
            ambeo_api = await AmbeoAPIFactory.create_api(
                host, port, client_session, hass)
            name = await ambeo_api.get_name()
            serial = await ambeo_api.get_serial()
            return name, serial, None
        except Exception as error:
            _LOGGER.error("Connection error to %s: %s", host, error)
            return None, None, "cannot_connect"


class AmbeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options configuration for Ambeo Soundbar integration."""

    async def async_step_init(self, user_input=None):
        errors = {}
        host_default = self.config_entry.options.get(
            CONFIG_HOST, self.config_entry.data.get(CONFIG_HOST))
        if user_input is not None:
            name, serial, error = await validate_connection(self.hass, user_input[CONFIG_HOST])
            if error is not None:
                errors["base"] = error
                return self.display_form(errors, host_default)
            else:
                return self.async_create_entry(data=user_input)

        return self.display_form(errors, host_default)

    def display_form(self, errors, host_default):

        try:
            support_debounce = self.hass.data[DOMAIN][self.config_entry.entry_id]["api"].support_debounce_mode(
            )
        except:
            support_debounce = False

        if self.config_entry.options.get(CONFIG_DEBOUNCE_COOLDOWN, 0) > 0:
            errors["base"] = "experimental_feature_activated"
        options_schema = vol.Schema({
            vol.Optional(CONFIG_HOST, default=host_default): str,
            vol.Optional(CONFIG_DEBOUNCE_COOLDOWN, default=self.config_entry.options.get(CONFIG_DEBOUNCE_COOLDOWN, CONFIG_DEBOUNCE_COOLDOWN_DEFAULT)): int,
        }) if support_debounce else vol.Schema({
            vol.Optional(CONFIG_HOST, default=host_default): str})

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
            host = user_input.get(CONFIG_HOST)
            name, serial, error = await validate_connection(self.hass, host)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONFIG_HOST, default=CONFIG_HOST_DEFAULT): str
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
