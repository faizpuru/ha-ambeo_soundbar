"""Tests for the Ambeo HTTP transport."""

import json

import aiohttp
import pytest
import yarl

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


def _only_url(mock_http):
    """Return the URL of the single recorded request."""
    ((_, url),) = mock_http.requests
    return url


def _spy_get(monkeypatch, session) -> list[yarl.URL]:
    """Record the URLs passed to session.get, as aiohttp will send them."""
    urls: list[yarl.URL] = []
    original = session.get

    def get(url, **kwargs):
        urls.append(yarl.URL(url))
        return original(url, **kwargs)

    monkeypatch.setattr(session, "get", get)
    return urls


async def test_create_event_queue_encoding(mock_http, session, monkeypatch):
    """Send the subscription percent-encoded exactly once."""
    urls = _spy_get(monkeypatch, session)
    mock_http.get(url_for("event/modifyQueue"), payload="{queue-1}")
    await AmbeoTransport(HOST, session).create_event_queue(["player:volume"])
    (url,) = urls
    # Reserved characters stay encoded: no decoding, no double encoding.
    assert "%22path%22%3A%20%22player%3Avolume%22" in url.raw_query_string
    assert "%25" not in url.raw_query_string
    assert json.loads(url.query["subscribe"]) == [
        {"path": "player:volume", "type": "itemWithValue"}
    ]


async def test_poll_event_queue_encoding(mock_http, session, monkeypatch):
    """Send the queue ID percent-encoded exactly once, with the timeout."""
    urls = _spy_get(monkeypatch, session)
    mock_http.get(url_for("event/pollQueue"), payload=[])
    await AmbeoTransport(HOST, session).poll_event_queue("{q/1}", timeout_ms=5000)
    (url,) = urls
    assert "queueId=%7Bq%2F1%7D" in url.raw_query_string
    assert url.query["queueId"] == "{q/1}"
    assert url.query["timeout"] == "5000"


async def test_create_event_queue_unexpected(mock_http, transport):
    """Return None when the device does not answer a queue ID."""
    mock_http.get(url_for("event/modifyQueue"), payload={"error": "x"})
    assert await transport.create_event_queue(["player:volume"]) is None


async def test_poll_event_queue_unexpected(mock_http, transport):
    """Return None when the poll answer is not a list."""
    mock_http.get(url_for("event/pollQueue"), payload={"error": "x"})
    assert await transport.poll_event_queue("q") is None


async def test_html_response(mock_http, transport):
    """Raise AmbeoResponseError on a non-JSON answer."""
    mock_http.get(url_for("getData"), body="<html></html>", content_type="text/html")
    with pytest.raises(AmbeoResponseError):
        await transport.get_data("player:volume")


async def test_invalid_json(mock_http, transport):
    """Raise AmbeoResponseError on malformed JSON."""
    mock_http.get(url_for("getData"), body="{not json", content_type="application/json")
    with pytest.raises(AmbeoResponseError):
        await transport.get_data("player:volume")


async def test_activate(mock_http, transport):
    """Send the action payload with the activate role."""
    mock_http.get(url_for("setData", "player:player/control"), payload=None)
    await transport.activate("player:player/control", {"control": "play"})
    url = _only_url(mock_http)
    assert url.query["roles"] == "activate"
    assert json.loads(url.query["value"]) == {"control": "play"}


async def test_get_rows_range(mock_http, transport):
    """Pass the requested row range."""
    mock_http.get(url_for("getRows", "ui:/inputs"), payload={"rows": []})
    assert await transport.get_rows("ui:/inputs", 2, 5) == []
    url = _only_url(mock_http)
    assert (url.query["from"], url.query["to"]) == ("2", "5")
