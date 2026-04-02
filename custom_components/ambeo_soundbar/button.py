"""Button entities for Ambeo Soundbar integration."""

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from .api.const import Capability
from .const import DOMAIN
from .entity import AmbeoBaseEntity


class AmbeoReboot(AmbeoBaseEntity, ButtonEntity):
    """Button to reboot the device."""

    def __init__(self, coordinator, device):
        """Initialize the reboot button."""
        super().__init__(coordinator, device, "Ambeo Reboot", "ambeo_reboot")

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_reboot()

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

    def __init__(self, coordinator, device):
        """Initialize the reset expert settings button."""
        super().__init__(
            coordinator, device, "Reset Expert Settings", "reset_expert_settings"
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_reset_expert_settings()

    @property
    def entity_category(self) -> EntityCategory:
        """Return the entity category."""
        return EntityCategory.CONFIG


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up the button entities from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ambeo_device = hass.data[DOMAIN][config_entry.entry_id]["device"]
    entities: list[AmbeoBaseEntity] = [AmbeoReboot(coordinator, ambeo_device)]
    if coordinator.has_capability(Capability.RESET_EXPERT_SETTINGS):
        entities.append(ResetExpertSettings(coordinator, ambeo_device))
    async_add_entities(entities)
