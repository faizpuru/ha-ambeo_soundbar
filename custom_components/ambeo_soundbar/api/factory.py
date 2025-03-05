import logging

from aiohttp import ClientSession
from .impl.espresso_api import AmbeoEspressoApi
from .impl.popcorn_api import AmbeoPopcornApi
from .impl.generic_api import AmbeoApi
from ..const import POPCORN_API_MODELS, ESPRESSO_API_MODELS

_LOGGER = logging.getLogger(__name__)


class AmbeoAPIFactory:
    """Factory to get the correct API depending on model"""

    @staticmethod
    async def create_api(ip: str, port, session: ClientSession, hass) -> AmbeoApi:
        ambeo_api = AmbeoApi(ip, port, session, hass)
        model = await ambeo_api.get_model()
        _LOGGER.debug("Setting up the API for " + model)
        if model in POPCORN_API_MODELS:
            return AmbeoPopcornApi(ip, port, session, hass)
        elif model in ESPRESSO_API_MODELS:
            return AmbeoEspressoApi(ip, port, session, hass)
        else:
            raise ValueError(f"Unsupported model : {model}")
