"""Tests for the Ambeo HTTP transport."""

import aiohttp
import pytest

from custom_components.ambeo_soundbar.api.exceptions import (
    AmbeoConnectionError,
    AmbeoResponseError,
    AmbeoTimeoutError,
)
from custom_components.ambeo_soundbar.api.transport import AmbeoTransport

from .conftest import HOST, mock_value, url_for


@pytest.fixture
def transport(session):
    """Return a transport bound to the test host."""
    return AmbeoTransport(HOST, session)


async def test_get_value(mock_http, transport):
    """Return the typed value of a path."""
    mock_value(mock_http, "player:volume", "i32_", 42)
    assert await transport.get_value("player:volume", "i32_") == 42


async def test_get_value_missing_type(mock_http, transport):
    """Raise when the response does not hold the requested type."""
    mock_value(mock_http, "player:volume", "i32_", 42)
    with pytest.raises(AmbeoResponseError):
        await transport.get_value("player:volume", "bool_")


async def test_http_error_status(mock_http, transport):
    """Raise AmbeoResponseError with the status on non-200 responses."""
    mock_http.get(url_for("getData", "player:volume"), status=500)
    with pytest.raises(AmbeoResponseError) as err:
        await transport.get_value("player:volume", "i32_")
    assert err.value.status == 500


async def test_timeout(mock_http, transport):
    """Raise AmbeoTimeoutError on timeouts."""
    mock_http.get(url_for("getData", "player:volume"), exception=TimeoutError())
    with pytest.raises(AmbeoTimeoutError):
        await transport.get_value("player:volume", "i32_")


async def test_connection_error(mock_http, transport):
    """Raise AmbeoConnectionError on client errors."""
    mock_http.get(
        url_for("getData", "player:volume"),
        exception=aiohttp.ClientConnectionError(),
    )
    with pytest.raises(AmbeoConnectionError) as err:
        await transport.get_value("player:volume", "i32_")
    assert not isinstance(err.value, AmbeoTimeoutError)


async def test_set_value_sends_json(mock_http, transport):
    """Send the typed value as JSON."""
    mock_http.get(url_for("setData", "player:volume"), payload=None)
    await transport.set_value("player:volume", "i32_", 12)
    (method, url), _ = next(iter(mock_http.requests.items()))
    assert url.query["value"] == '{"type": "i32_", "i32_": 12}'
    assert url.query["roles"] == "value"


async def test_get_rows_missing(mock_http, transport):
    """Raise when getRows has no rows."""
    mock_http.get(url_for("getRows", "ui:/inputs"), payload={})
    with pytest.raises(AmbeoResponseError):
        await transport.get_rows("ui:/inputs", 0, 10)


async def test_create_event_queue(mock_http, transport):
    """Return the queue ID."""
    mock_http.get(url_for("event/modifyQueue"), payload="{queue-1}")
    assert await transport.create_event_queue(["player:volume"]) == "{queue-1}"


async def test_poll_event_queue_events(mock_http, transport):
    """Return the polled events."""
    mock_http.get(url_for("event/pollQueue"), payload=[{"path": "x"}])
    assert await transport.poll_event_queue("q") == [{"path": "x"}]


async def test_poll_event_queue_timeout(mock_http, transport):
    """A timeout means no events: the queue is still valid."""
    mock_http.get(url_for("event/pollQueue"), exception=TimeoutError())
    assert await transport.poll_event_queue("q") == []


async def test_poll_event_queue_lost(mock_http, transport):
    """Any other error means the queue is lost."""
    mock_http.get(url_for("event/pollQueue"), status=500)
    assert await transport.poll_event_queue("q") is None


async def test_closed_session():
    """Raise AmbeoConnectionError when the session is closed."""
    session = aiohttp.ClientSession()
    await session.close()
    with pytest.raises(AmbeoConnectionError):
        await AmbeoTransport(HOST, session).get_data("player:volume")
