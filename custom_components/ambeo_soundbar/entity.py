import logging

from .const import DOMAIN, BRIGHTNESS_SCALE
from homeassistant.components.light import LightEntity, COLOR_MODE_BRIGHTNESS
from homeassistant.components.switch import SwitchEntity
from homeassistant.util.color import value_to_brightness

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers.entity import Entity

class AmbeoBaseEntity(Entity):
    """Classe de base pour les entités Ambeo."""

    def __init__(self, device, api, name_suffix, unique_id_suffix):
        """Initialiser l'entité de base."""
        self._name = f"{device.name} {name_suffix}"
        self.api = api
        self._unique_id = f"{device.serial}_{unique_id_suffix.lower().replace(' ', '_')}"
        self.ambeo_device = device

    @property
    def device_info(self):
        """Retourner les informations de l'appareil."""
        return {
            "identifiers": {(DOMAIN, self.ambeo_device.serial)},
        }

    @property
    def unique_id(self):
        """Retourner l'identifiant unique pour l'entité."""
        return self._unique_id

    @property
    def name(self):
        """Retourner le nom de l'entité."""
        return self._name

class BaseLight(AmbeoBaseEntity, LightEntity):
    def __init__(self, device, api, name_suffix, unique_id_suffix):
        super().__init__(device, api, name_suffix, unique_id_suffix)
        self._brightness = 0  # Spécifique aux entités de type lumière

    @property
    def is_on(self):
        return self._brightness > 0

    @property
    def supported_color_modes(self):
        return {COLOR_MODE_BRIGHTNESS}

    @property
    def color_mode(self):
        return COLOR_MODE_BRIGHTNESS

    @property
    def brightness(self):
        return value_to_brightness(BRIGHTNESS_SCALE, self._brightness)


class AmbeoBaseSwitch(AmbeoBaseEntity, SwitchEntity):
    """La classe reste principalement inchangée."""

    def __init__(self, device, api, feature_name):
        super().__init__(device, api, feature_name, feature_name)
        self._is_on = True 

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on
