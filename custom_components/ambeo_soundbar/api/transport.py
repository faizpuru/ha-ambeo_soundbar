"""HTTP transport for the Ambeo Soundbar API."""

import json
import logging
import time
from typing import Any
from urllib.parse import quote

import aiohttp
import yarl

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT
from .exceptions import (
    AmbeoConnectionError,
    AmbeoResponseError,
    AmbeoTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


def _nocache() -> int:
    """Generate a nocache parameter to prevent caching."""
    return int(time.time() * 1000)


class AmbeoTransport:
    """Low-level access to the soundbar HTTP API."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the transport."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._session = session
        self._endpoint = f"http://{host}:{port}/api"

    async def _fetch(
        self, url: str, http_timeout: float | None = None, encoded: bool = False
    ) -> Any:
        """Fetch a relative URL and return the decoded JSON body.

        Args:
            url: Relative URL path (appended to the API endpoint).
            http_timeout: Override the default HTTP timeout (seconds).
            encoded: If True, treat the URL as already percent-encoded and pass
                it to aiohttp as a yarl.URL(…, encoded=True) to prevent
                double-encoding of special characters such as { and }.

        """
        full_url = f"{self._endpoint}/{url}"
        total = http_timeout if http_timeout is not None else self.timeout
        request_url: str | yarl.URL = (
            yarl.URL(full_url, encoded=True) if encoded else full_url
        )
        _LOGGER.debug("Executing URL fetch: %s", full_url)
        try:
            async with self._session.get(
                request_url, timeout=aiohttp.ClientTimeout(total=total)
            ) as response:
                if response.status != 200:
                    raise AmbeoResponseError(
                        f"HTTP {response.status} for url: {full_url}",
                        status=response.status,
                    )
                return await response.json()
        except TimeoutError as e:
            raise AmbeoTimeoutError(f"Timeout fetching url: {full_url}") from e
        except aiohttp.ContentTypeError as e:
            raise AmbeoResponseError(f"Non-JSON response for url: {full_url}") from e
        except aiohttp.ClientError as e:
            raise AmbeoConnectionError(
                f"Client error for url: {full_url}. Exception: {e}"
            ) from e
        except ValueError as e:
            raise AmbeoResponseError(f"Invalid JSON for url: {full_url}") from e
        except RuntimeError as e:
            # aiohttp raises RuntimeError when the session is closed.
            raise AmbeoConnectionError(
                f"Session error for url: {full_url}. Exception: {e}"
            ) from e

    async def request(
        self,
        function: str,
        path: str,
        role: str | None = None,
        value: str | None = None,
        from_idx: int | None = None,
        to_idx: int | None = None,
    ) -> Any:
        """Execute a request with the specified parameters."""
        url = f"{function}?path={path}"
        if role:
            url += f"&roles={role}"
        if value is not None:
            url += f"&value={value}"
        if from_idx is not None:
            url += f"&from={from_idx}"
        if to_idx is not None:
            url += f"&to={to_idx}"
        url += f"&_nocache={_nocache()}"
        return await self._fetch(url)

    async def get_data(self, path: str, role: str = "@all") -> Any:
        """Return the raw getData response for a path."""
        return await self.request("getData", path, role)

    async def get_value(self, path: str, data_type: str) -> Any:
        """Get a value of a specified type from a specified path."""
        data = await self.get_data(path)
        try:
            return data["value"][data_type]
        except (KeyError, TypeError) as e:
            raise AmbeoResponseError(
                f"Missing value '{data_type}' for path: {path}"
            ) from e

    async def set_value(self, path: str, data_type: str, value: Any) -> None:
        """Set a value of a specified type at a specified path."""
        await self.request(
            "setData", path, "value", json.dumps({"type": data_type, data_type: value})
        )

    async def activate(self, path: str, payload: dict[str, Any]) -> None:
        """Trigger an action path with the given payload."""
        await self.request("setData", path, "activate", json.dumps(payload))

    async def get_rows(self, path: str, from_idx: int, to_idx: int) -> list[dict]:
        """Return the rows of a list path."""
        data = await self.request("getRows", path, "@all", None, from_idx, to_idx)
        rows = data.get("rows") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise AmbeoResponseError(f"Missing rows for path: {path}")
        return rows

    async def create_event_queue(self, paths: list[str]) -> str | None:
        """Create an event subscription queue and return the queue ID."""
        subscribe_json = json.dumps(
            [{"path": p, "type": "itemWithValue"} for p in paths]
        )
        subscribe_encoded = quote(subscribe_json, safe="")
        url = f"event/modifyQueue?subscribe={subscribe_encoded}&_nocache={_nocache()}"
        result = await self._fetch(url, encoded=True)
        if isinstance(result, str):
            return result
        return None

    async def poll_event_queue(
        self, queue_id: str, timeout_ms: int = 30000
    ) -> list | None:
        """Poll an event queue for changes. Blocks until events arrive or timeout.

        Returns a (possibly empty) list of events, or None on any error or
        expiry — the caller should recreate the queue in that case.
        """
        queue_id_encoded = quote(queue_id, safe="")
        http_timeout = timeout_ms // 1000 + 10
        url = f"event/pollQueue?queueId={queue_id_encoded}&timeout={timeout_ms}&_nocache={_nocache()}"
        try:
            result = await self._fetch(url, http_timeout=http_timeout, encoded=True)
        except AmbeoTimeoutError:
            # Poll simply expired, the queue is still valid on the device.
            return []
        except (AmbeoConnectionError, AmbeoResponseError):
            # Any other error (connection refused, etc.) signals the queue is lost.
            return None
        if isinstance(result, list):
            return result
        return None
