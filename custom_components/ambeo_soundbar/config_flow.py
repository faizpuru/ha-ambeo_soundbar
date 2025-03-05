import logging
import voluptuous as vol
import aiohttp


from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_PORT
from .api.factory import AmbeoAPIFactory


_LOGGER = logging.getLogger(__name__)


class AmbeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Gère la configuration des options pour l'intégration Ambeo Soundbar."""

    def __init__(self, config_entry):
        """Initialise le gestionnaire d'options avec la configuration existante."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Gestion de la configuration des options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        host_default = self.config_entry.data.get("host")
        options_schema = vol.Schema({
            vol.Optional("host", default=host_default): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors={}
        )


class AmbeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Manage the configuration flow """

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a configuration initiated by the user."""
        errors = {}

        if user_input is not None:
            host = user_input.get("host")
            ambeo_api = await AmbeoAPIFactory.create_api(
                host, DEFAULT_PORT, aiohttp.ClientSession(), self.hass)
            name = await ambeo_api.get_name()
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
        return AmbeoOptionsFlowHandler(config_entry)
