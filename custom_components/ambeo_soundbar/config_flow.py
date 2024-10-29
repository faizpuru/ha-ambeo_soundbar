
import logging
import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AmbeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Manage the configuration flow """

    async def async_step_user(self, user_input=None):
        """Handle a configuration initiated by the user."""
        errors = {}

        if user_input is not None:
            # If user input is provided, create an entry with the given input.
            return self.async_create_entry(title="Ambeo", data=user_input)

        # Define the data schema for the user form.
        # This example requires a "host" field.
        data_schema = vol.Schema({
            vol.Required("host"): str
        })

        # Display the form to the user.
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
