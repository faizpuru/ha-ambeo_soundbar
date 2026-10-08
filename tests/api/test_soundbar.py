"""Tests for the Ambeo soundbar models."""

import asyncio
import json
from unittest.mock import AsyncMock

import aiohttp
import pytest

from custom_components.ambeo_soundbar.api import (
    AmbeoConnectionError,
    AmbeoEspresso,
    AmbeoPopcorn,
    AmbeoResponseError,
    AmbeoSoundbar,
    AmbeoUnsupportedModelError,
    Capability,
    DeviceInfo,
    PlayerStatus,
    Preset,
    Source,
    StateKey,
)
from custom_components.ambeo_soundbar.api.transport import AmbeoTransport

from .conftest import HOST, mock_device_info, mock_rows, mock_value, url_for

PLUS = "AMBEO Soundbar Plus"
MAX = "AMBEO Soundbar Max"


def _make(cls, session, **kwargs):
    """Build a soundbar without connecting."""
    return cls(
        AmbeoTransport(HOST, session),
        DeviceInfo(cls.models[0], "name", "serial", "1.0"),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# connect()
# ---------------------------------------------------------------------------


async def test_connect_popcorn(mock_http, session):
    """Pick the Popcorn implementation and load info, sources and presets."""
    mock_device_info(mock_http, PLUS)
    mock_rows(mock_http, "ui:/inputs", [{"id": "hdmi1", "title": "HDMI 1"}])
    mock_rows(
        mock_http,
        "settings:/popcorn/audio/audioPresetValues",
        [{"title": "Movies", "value": {"popcornAudioPreset": "movies"}}],
    )

    bar = await AmbeoSoundbar.connect(HOST, session)

    assert isinstance(bar, AmbeoPopcorn)
    assert bar.info == DeviceInfo(PLUS, "Living room", "SN123", "1.2.3")
    assert bar.sources == [
        Source("hdmi1", "HDMI 1"),
        Source("airplay", "AirPlay"),
        Source("googlecast", "Google Cast"),
    ]
    assert bar.presets == [Preset("movies", "Movies")]


async def test_connect_espresso_sources(mock_http, session):
    """Map Max input names to input indexes, case-insensitively."""
    mock_device_info(mock_http, MAX)
    mock_rows(
        mock_http,
        "settings:/espresso/inputNames",
        [
            {"title": "HDMI1", "value": {"string_": "TV"}},
            {"title": "aes", "value": {"string_": "AES"}},
            {"title": "Optical", "value": {"string_": "Optical"}},
        ],
    )
    mock_rows(
        mock_http,
        "espresso:",
        [{"title": "aes"}, {"title": "hdmi1"}, {"title": "optical"}],
    )

    bar = await AmbeoSoundbar.connect(HOST, session)

    assert isinstance(bar, AmbeoEspresso)
    assert bar.sources == [Source(1, "TV"), Source(2, "Optical")]
    assert [p.title for p in bar.presets][:2] == ["Neutral", "Movies"]


async def test_connect_tolerates_missing_sources(mock_http, session):
    """Fall back to empty sources/presets when the device rejects them."""
    mock_device_info(mock_http, PLUS)
    mock_http.get(url_for("getRows"), status=404, repeat=True)

    bar = await AmbeoSoundbar.connect(HOST, session)

    assert bar.sources == []
    assert bar.presets == []


async def test_connect_unsupported_model(mock_http, session):
    """Raise for unknown models."""
    mock_device_info(mock_http, "AMBEO Soundbar Ultra")
    with pytest.raises(AmbeoUnsupportedModelError) as err:
        await AmbeoSoundbar.connect(HOST, session)
    assert err.value.model == "AMBEO Soundbar Ultra"


async def test_connect_on_other_subclass(mock_http, session):
    """Refuse a device of another model when called on a subclass."""
    mock_device_info(mock_http, MAX)
    with pytest.raises(AmbeoUnsupportedModelError):
        await AmbeoPopcorn.connect(HOST, session)


async def test_connect_model_unreadable(mock_http, session):
    """Report a device error, not an unsupported model, when the model is unreadable."""
    mock_http.get(url_for("getData"), status=500, repeat=True)
    with pytest.raises(AmbeoResponseError):
        await AmbeoSoundbar.connect(HOST, session)


async def test_connect_skips_malformed_espresso_rows(mock_http, session):
    """Ignore Max input rows missing their title or value."""
    mock_device_info(mock_http, MAX)
    mock_rows(
        mock_http,
        "settings:/espresso/inputNames",
        [
            {"title": "HDMI1", "value": {"string_": "TV"}},
            {"title": "optical"},
            {"value": {"string_": "No title"}},
        ],
    )
    mock_rows(mock_http, "espresso:", [{"title": "hdmi1"}, {}, {"title": "optical"}])

    bar = await AmbeoSoundbar.connect(HOST, session)

    assert bar.sources == [Source(0, "TV")]


async def test_connect_skips_malformed_popcorn_presets(mock_http, session):
    """Ignore Popcorn preset rows missing their title or value."""
    mock_device_info(mock_http, PLUS)
    mock_rows(mock_http, "ui:/inputs", [])
    mock_rows(
        mock_http,
        "settings:/popcorn/audio/audioPresetValues",
        [
            {"title": "Movies", "value": {"popcornAudioPreset": "movies"}},
            {"title": "Broken"},
            {"title": "Null", "value": None},
            {"value": {"popcornAudioPreset": "music"}},
        ],
    )

    bar = await AmbeoSoundbar.connect(HOST, session)

    assert bar.presets == [Preset("movies", "Movies")]


async def test_connect_unreachable(mock_http, session):
    """Propagate connection errors."""
    mock_http.get(
        url_for("getData"), exception=aiohttp.ClientConnectionError(), repeat=True
    )
    with pytest.raises(AmbeoConnectionError):
        await AmbeoSoundbar.connect(HOST, session)


# ---------------------------------------------------------------------------
# fetch_state()
# ---------------------------------------------------------------------------


async def test_fetch_state(mock_http, session):
    """Return core values and capability-filtered optional values."""
    bar = _make(AmbeoEspresso, session)
    mock_value(mock_http, "player:volume", "i32_", 20)
    mock_value(mock_http, "settings:/mediaPlayer/mute", "bool_", False)
    mock_value(mock_http, "powermanager:target", "powerTarget", {"target": "online"})
    mock_value(mock_http, "espresso:audioInputID", "i32_", 1)
    mock_value(mock_http, "settings:/espresso/equalizerPreset", "i32_", 4)
    mock_value(mock_http, "espresso:nightModeUi", "bool_", True)
    mock_value(
        mock_http,
        "settings:/espresso/brightnessSensor",
        "espressoBrightness",
        {"ambeologo": 10, "display": 20},
    )
    # Everything else is rejected by the device.
    mock_http.get(url_for("getData"), status=404, repeat=True)

    state = await bar.fetch_state()

    assert state[StateKey.VOLUME] == 20
    assert state[StateKey.MUTED] is False
    assert state[StateKey.STATE] == "online"
    assert state[StateKey.CURRENT_SOURCE] == 1
    assert state[StateKey.CURRENT_PRESET] == 4
    assert state[StateKey.PLAYER_DATA] is None
    assert state[StateKey.NIGHT_MODE] is True
    assert state[StateKey.DISPLAY_BRIGHTNESS] == 20
    assert state[StateKey.LOGO_BRIGHTNESS] == 10
    # Logo and display share one path: read it once.
    brightness_reads = [
        url
        for (method, url), calls in mock_http.requests.items()
        for _ in calls
        if url.query.get("path") == "settings:/espresso/brightnessSensor"
    ]
    assert len(brightness_reads) == 1
    # Popcorn-only capability, never fetched on the Max.
    assert StateKey.LED_BAR_BRIGHTNESS not in state
    # Rejected optional value is left out.
    assert StateKey.AMBEO_MODE not in state


async def test_fetch_state_unreachable(mock_http, session):
    """Propagate connection errors on core values."""
    bar = _make(AmbeoPopcorn, session)
    mock_http.get(
        url_for("getData"), exception=aiohttp.ClientConnectionError(), repeat=True
    )
    with pytest.raises(AmbeoConnectionError):
        await bar.fetch_state()


# ---------------------------------------------------------------------------
# player_status()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cls", "state", "expected"),
    [
        (AmbeoEspresso, {"state": "networkStandby"}, PlayerStatus.STANDBY),
        (AmbeoPopcorn, {"state": "networkStandby"}, PlayerStatus.IDLE),
        (AmbeoPopcorn, {"state": None}, PlayerStatus.ON),
        (
            AmbeoPopcorn,
            {"state": "online", "player_data": {"state": "paused"}},
            PlayerStatus.PAUSED,
        ),
        (
            AmbeoPopcorn,
            {"state": "online", "decoder_status": {"channels": 2}},
            PlayerStatus.PLAYING,
        ),
        (
            AmbeoEspresso,
            {"state": "online", "decoder_status": {"decoder_status": 0}},
            PlayerStatus.IDLE,
        ),
        (
            AmbeoPopcorn,
            {"state": "online", "player_data": {"state": "playing"}},
            PlayerStatus.PLAYING,
        ),
        (
            AmbeoPopcorn,
            {"state": "online", "player_data": {"state": "unknown"}},
            PlayerStatus.IDLE,
        ),
    ],
)
async def test_player_status(session, cls, state, expected):
    """Derive the playback status from a state snapshot."""
    assert _make(cls, session).player_status(state) == expected


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


async def test_subscribed_paths(session):
    """Subscribe to base paths and capability-filtered model paths."""
    popcorn = _make(AmbeoPopcorn, session).subscribed_paths()
    espresso = _make(AmbeoEspresso, session).subscribed_paths()

    assert "powermanager:target" in popcorn
    assert "bluetooth:state" in popcorn
    assert "settings:/espresso/brightnessSensor" not in popcorn
    assert "settings:/espresso/brightnessSensor" in espresso
    assert "bluetooth:state" not in espresso


async def test_process_event(session):
    """Map event values to state keys."""
    popcorn = _make(AmbeoPopcorn, session)
    espresso = _make(AmbeoEspresso, session)

    assert popcorn.process_event(
        "powermanager:target", {"powerTarget": {"target": "online"}}
    ) == {StateKey.STATE: "online"}
    assert popcorn.process_event(
        "bluetooth:state", {"bluetoothState": {"pairable": True}}
    ) == {StateKey.BLUETOOTH_PAIRING: True}
    assert espresso.process_event(
        "settings:/espresso/brightnessSensor",
        {"espressoBrightness": {"ambeologo": 5, "display": 7}},
    ) == {StateKey.LOGO_BRIGHTNESS: 5, StateKey.DISPLAY_BRIGHTNESS: 7}
    assert (
        espresso.process_event(
            "settings:/espresso/brightnessSensor", {"espressoBrightness": None}
        )
        == {}
    )
    assert popcorn.process_event("unknown:path", {"i32_": 1}) == {}


async def test_listen(session):
    """Yield batched updates and recreate the queue when it is lost."""
    bar = _make(AmbeoPopcorn, session)
    transport = bar._transport
    transport.create_event_queue = AsyncMock(side_effect=["q1", "q2"])
    transport.poll_event_queue = AsyncMock(
        side_effect=[
            [
                {
                    "itemType": "update",
                    "path": "player:volume",
                    "itemValue": {"i32_": 3},
                },
                {
                    "itemType": "update",
                    "path": "settings:/mediaPlayer/mute",
                    "itemValue": {"bool_": True},
                },
                {"itemType": "add", "path": "player:volume", "itemValue": {"i32_": 9}},
            ],
            [],
            None,
            [{"itemType": "update", "path": "player:volume", "itemValue": {"i32_": 4}}],
        ]
    )

    listener = bar.listen(retry_delay=0)
    assert await anext(listener) == {StateKey.VOLUME: 3, StateKey.MUTED: True}
    assert await anext(listener) == {StateKey.VOLUME: 4}
    await listener.aclose()

    assert [c.args[0] for c in transport.create_event_queue.call_args_list] == [
        bar.subscribed_paths(),
        bar.subscribed_paths(),
    ]
    assert transport.poll_event_queue.call_args_list[-1].args[0] == "q2"


async def test_listen_retries_queue_creation(session):
    """Retry queue creation after a delay when it fails."""
    bar = _make(AmbeoPopcorn, session)
    transport = bar._transport
    transport.create_event_queue = AsyncMock(
        side_effect=[AmbeoConnectionError("down"), None, "q"]
    )
    transport.poll_event_queue = AsyncMock(
        return_value=[
            {"itemType": "update", "path": "player:volume", "itemValue": {"i32_": 1}}
        ]
    )

    update = await asyncio.wait_for(anext(bar.listen(retry_delay=0)), 1)

    assert update == {StateKey.VOLUME: 1}
    assert transport.create_event_queue.await_count == 3


async def test_has_capability(session):
    """Capabilities accept enum members and raw strings."""
    bar = _make(AmbeoEspresso, session)
    assert bar.has_capability(Capability.STANDBY)
    assert bar.has_capability("standby")
    assert not bar.has_capability(Capability.LED_BAR)


def _set_data_values(mock_http) -> list[dict]:
    """Return the JSON values sent with setData requests."""
    return [
        json.loads(url.query["value"])
        for (method, url) in mock_http.requests
        if url.path.endswith("/setData")
    ]


async def test_set_logo_brightness_keeps_display(mock_http, session):
    """Write the new logo brightness along with the current display brightness."""
    bar = _make(AmbeoEspresso, session)
    mock_value(
        mock_http,
        "settings:/espresso/brightnessSensor",
        "espressoBrightness",
        {"ambeologo": 10, "display": 20},
    )
    mock_http.get(url_for("setData"), payload=None)

    await bar.set_logo_brightness(5)

    assert _set_data_values(mock_http) == [
        {
            "type": "espressoBrightness",
            "espressoBrightness": {"ambeologo": 5, "display": 20},
        }
    ]


async def test_set_brightness_missing_value(mock_http, session):
    """Refuse to overwrite the other brightness when it cannot be read."""
    bar = _make(AmbeoEspresso, session)
    mock_value(
        mock_http,
        "settings:/espresso/brightnessSensor",
        "espressoBrightness",
        {"ambeologo": 10},
    )

    with pytest.raises(AmbeoResponseError):
        await bar.set_logo_brightness(5)
    assert _set_data_values(mock_http) == []
