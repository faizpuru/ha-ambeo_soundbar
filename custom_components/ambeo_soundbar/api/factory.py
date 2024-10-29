import logging
from .impl.max_api import AmbeoApiMax
from .impl.plus_api import AmbeoApiPlus
from .impl.generic_api import AmbeoApi
from homeassistant.exceptions import ConfigEntryNotReady
from ..const import MAX_SOUNDBAR, PLUS_SOUNDBAR

_LOGGER = logging.getLogger(__name__)


class AmbeoAPIFactory:
    """Factory to get the correct API depending on model"""

    @staticmethod
    async def create_api(ip, port, session, hass) -> AmbeoApi:
        ambeo_api = AmbeoApi(ip, port, session, hass)
        serial = await ambeo_api.get_serial()
        if serial is None:
            raise ConfigEntryNotReady(f"Can't connect to host : {ip}")
        model = await ambeo_api.get_model()
        _LOGGER.debug("Setting up the API for " + model)
        if model == PLUS_SOUNDBAR:
            return AmbeoApiPlus(ip, port, session, hass)
        elif model == MAX_SOUNDBAR:
            return AmbeoApiMax(ip, port, session, hass)
        else:
            raise ValueError(f"Unsupported model : {model}")
