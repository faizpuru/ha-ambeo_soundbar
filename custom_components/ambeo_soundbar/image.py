"""Image entity for Ambeo Soundbar integration."""

from homeassistant.components.image import ImageEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util
from pyambeo import AmbeoError

from . import AmbeoConfigEntry, AmbeoDevice
from .const import DOMAIN
from .coordinator import AmbeoCoordinator
from .entity import AmbeoBaseEntity

PARALLEL_UPDATES = 0


class ProductPicture(AmbeoBaseEntity, ImageEntity):
    """Picture of the soundbar, as shown by its web app.

    The picture never changes: it is downloaded once, then cached.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: AmbeoCoordinator, device: AmbeoDevice, url: str
    ) -> None:
        """Initialize the product picture."""
        super().__init__(coordinator, device, "product_picture", "product_picture")
        ImageEntity.__init__(self, coordinator.hass)
        self._attr_image_url = url
        self._attr_image_last_updated = dt_util.utcnow()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: AmbeoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the product picture from a config entry."""
    coordinator = config_entry.runtime_data.coordinator
    try:
        url = await coordinator.fetch_image_url()
    except AmbeoError as err:
        raise PlatformNotReady(
            translation_domain=DOMAIN,
            translation_key="update_failed",
            translation_placeholders={"error": str(err)},
        ) from err
    if url:
        async_add_entities(
            [ProductPicture(coordinator, config_entry.runtime_data.device, url)]
        )
