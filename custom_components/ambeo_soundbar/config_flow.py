"""Config flow for Ambeo Soundbar integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)
from pyambeo import AmbeoError, AmbeoSoundbar, AmbeoUnsupportedModelError

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

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

_LOGGER = logging.getLogger(__name__)


async def validate_connection(
    hass: HomeAssistant, host: str, port: int = DEFAULT_PORT
) -> tuple[str | None, str | None, str | None]:
    """Validate connection to Ambeo device and return name if successful."""
    client_session = async_get_clientsession(hass)
    try:
        ambeo_api = await AmbeoSoundbar.connect(
            host, client_session, port=port, timeout=TIMEOUT
        )
        return ambeo_api.info.name, ambeo_api.info.serial, None
    except AmbeoUnsupportedModelError as error:
        _LOGGER.error("Unsupported device at %s: %s", host, error)
        return None, None, "unsupported_model"
    except AmbeoError as error:
        _LOGGER.error("Connection error to %s: %s", host, error)
        return None, None, "cannot_connect"
    except Exception:
        _LOGGER.exception("Unexpected error connecting to %s", host)
        return None, None, "unknown"


def _host_schema(default: str) -> vol.Schema:
    """Build the schema asking for the soundbar host."""
    return vol.Schema({vol.Required(CONFIG_HOST, default=default): TextSelector()})


class AmbeoOptionsFlowHandler(OptionsFlow):
    """Handle options configuration for Ambeo Soundbar integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of the options flow."""
        if user_input is not None:
            return self.async_create_entry(
                data={key: int(value) for key, value in user_input.items()}
            )

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONFIG_UPDATE_INTERVAL,
                    default=options.get(
                        CONFIG_UPDATE_INTERVAL, CONFIG_UPDATE_INTERVAL_DEFAULT
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=3600,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONFIG_CONCURRENT_REQUESTS,
                    default=options.get(
                        CONFIG_CONCURRENT_REQUESTS, CONFIG_CONCURRENT_REQUESTS_DEFAULT
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=10, mode=NumberSelectorMode.BOX)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class AmbeoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Manage the configuration flow for Ambeo Soundbar integration."""

    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a configuration initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONFIG_HOST]
            name, serial, error = await validate_connection(self.hass, host)
            if error:
                errors["base"] = error
            elif not serial:
                return self.async_abort(reason="no_serial")
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name or "Ambeo Soundbar", data={CONFIG_HOST: host}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_host_schema(CONFIG_HOST_DEFAULT),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a soundbar discovered over zeroconf."""
        serial = discovery_info.properties.get("serial")
        if not serial:
            return self.async_abort(reason="no_serial")

        host = discovery_info.host
        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured(updates={CONFIG_HOST: host})

        name, _, error = await validate_connection(self.hass, host)
        if error:
            return self.async_abort(reason=error)

        self._discovered_host = host
        self._discovered_name = name or "Ambeo Soundbar"
        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm the setup of a discovered soundbar."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name, data={CONFIG_HOST: self._discovered_host}
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._discovered_name,
                "host": self._discovered_host,
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the host of an existing soundbar."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            host = user_input[CONFIG_HOST]
            _, serial, error = await validate_connection(self.hass, host)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_mismatch(reason="different_device")
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONFIG_HOST: host}
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_host_schema(entry.data[CONFIG_HOST]),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> AmbeoOptionsFlowHandler:
        """Get the options flow for this handler."""
        return AmbeoOptionsFlowHandler()
