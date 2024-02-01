import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN 
from .const import VERSION 


class AmbeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer le flux de configuration de Mon Appareil."""

    async def async_step_user(self, user_input=None):
        """Gérer une configuration initiée par l'utilisateur."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="Ambeo", data=user_input)

        data_schema = vol.Schema({
            vol.Required("host"): str
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )