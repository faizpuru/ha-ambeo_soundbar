import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api.impl.generic_api import AmbeoApi
from .api.factory import AmbeoAPIFactory

_LOGGER = logging.getLogger(__name__)


class AmbeoCoordinator(DataUpdateCoordinator):

    _model: str = ""
    _serial: str = ""
    _name: str = ""
    _version: str = ""
    _api: AmbeoApi = ""

    def __init__(self, hass, host: str, port: int, client_session, interval):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ambeo coordinator",
            update_interval=timedelta(seconds=interval),
            always_update=True
        )
        self._host = host
        self._port = port
        self._client_session = client_session
        self._hass = hass

    def api(self) -> AmbeoApi:
        return self._api

    async def _async_setup(self):
        self._api = await AmbeoAPIFactory.create_api(
            self._host, self._port, self._client_session, self._hass)
        self._model = await self._api.get_model()
        self._serial = await self._api.get_serial()
        self._name = await self._api.get_name()
        self._version = await self._api.get_version()

    async def _async_update_data(self):
        pass

    def get_model(self) -> str:
        return self._model

    def get_serial(self) -> str:
        return self._serial

    def get_name(self) -> str:
        return self._name

    def get_version(self) -> str:
        return self._version

    def get_api(self) -> AmbeoApi:
        return self._api
