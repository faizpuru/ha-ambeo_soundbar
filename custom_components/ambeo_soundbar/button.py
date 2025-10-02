from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from .entity import AmbeoBaseEntity
from .const import DOMAIN, Capability
from .api.impl.generic_api import AmbeoApi


class AmbeoReboot(AmbeoBaseEntity, ButtonEntity):
    """The class remains largely unchanged."""

    def __init__(self, device, api):
        """Initialize the switch entity."""
        super().__init__(device, api, "Ambeo Reboot", "ambeo_reboot")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.api.reboot()

    @property
    def entity_category(self) -> EntityCategory:
        """Return the entity category."""
        return EntityCategory.CONFIG

    @property
    def device_class(self) -> ButtonDeviceClass:
        """Return the device class."""
        return ButtonDeviceClass.RESTART


class ResetExpertSettings(AmbeoBaseEntity, ButtonEntity):
    """Button to reset expert audio settings."""

    def __init__(self, device, api):
        """Initialize the reset expert settings button."""
        super().__init__(device, api, "Reset Expert Settings", "reset_expert_settings")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.api.reset_expert_settings()

    @property
    def entity_category(self) -> EntityCategory:
        """Return the entity category."""
        return EntityCategory.CONFIG

    @property
    def device_class(self) -> ButtonDeviceClass:
        """Return the device class."""
        return ButtonDeviceClass.RESTART


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the button entities from a config entry created in the integrations UI."""
    ambeo_api: AmbeoApi = hass.data[DOMAIN][config_entry.entry_id]["api"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities = [AmbeoReboot(ambeo_device, ambeo_api)]
    if ambeo_api.has_capability(Capability.RESET_EXPERT_SETTINGS):
        entities.append(ResetExpertSettings(ambeo_device, ambeo_api))
    async_add_entities(entities)
