"""Tests pinning the device API calls of each soundbar model."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ambeo_soundbar.api import (
    AmbeoEspresso,
    AmbeoPopcorn,
    AmbeoResponseError,
    DeviceInfo,
)
from custom_components.ambeo_soundbar.api.transport import AmbeoTransport

PRESS = {"type": "bool_", "bool_": True}


def _make(cls):
    """Build a soundbar on a mocked transport."""
    transport = MagicMock(spec=AmbeoTransport)
    return cls(transport, DeviceInfo(cls.models[0], None, None, None)), transport


@pytest.mark.parametrize(
    ("method", "arg", "path", "data_type", "value"),
    [
        ("set_volume", 20, "player:volume", "i32_", 20),
        ("set_mute", True, "settings:/mediaPlayer/mute", "bool_", True),
        ("set_source", 2, "espresso:audioInputID", "i32_", 2),
        ("set_preset", 4, "settings:/espresso/equalizerPreset", "i32_", 4),
        ("set_night_mode", True, "espresso:nightModeUi", "bool_", True),
        ("set_ambeo_mode", True, "espresso:ambeoModeUi", "bool_", True),
        ("set_ambeo_mode_level", 1, "settings:/espresso/ambeoMode", "i32_", 1),
        (
            "set_sound_feedback",
            False,
            "settings:/espresso/soundFeedback",
            "bool_",
            False,
        ),
        ("set_voice_enhancement_level", 3, "ui:/mydevice/voiceEnhanceLevel", "i16_", 3),
        ("set_center_speaker_level", 2, "ui:/settings/audio/centerSettings", "i16_", 2),
        ("set_side_firing_level", 2, "ui:/settings/audio/widthSettings", "i16_", 2),
        ("set_up_firing_level", 2, "ui:/settings/audio/heightSettings", "i16_", 2),
        ("set_subwoofer_status", True, "ui:/settings/subwoofer/enabled", "bool_", True),
        # The Max expects an integer subwoofer volume.
        ("set_subwoofer_volume", 3.0, "ui:/settings/subwoofer/volume", "i16_", 3),
        ("stand_by", None, "espresso:appRequestedStandby", "bool_", True),
        ("wake", None, "espresso:appRequestedOnline", "bool_", True),
    ],
)
async def test_espresso_set_value(method, arg, path, data_type, value):
    """Write each Max setting to its device path."""
    bar, transport = _make(AmbeoEspresso)
    args = () if arg is None else (arg,)
    await getattr(bar, method)(*args)
    transport.set_value.assert_awaited_once_with(path, data_type, value)


@pytest.mark.parametrize(
    ("method", "arg", "path", "data_type", "value"),
    [
        ("set_volume", 20, "player:volume", "i32_", 20),
        ("set_mute", True, "settings:/mediaPlayer/mute", "bool_", True),
        (
            "set_preset",
            "movie",
            "settings:/popcorn/audio/audioPresets/audioPreset",
            "popcornAudioPreset",
            "movie",
        ),
        (
            "set_night_mode",
            True,
            "settings:/popcorn/audio/nightModeStatus",
            "bool_",
            True,
        ),
        (
            "set_ambeo_mode",
            True,
            "settings:/popcorn/audio/ambeoModeStatus",
            "bool_",
            True,
        ),
        (
            "set_sound_feedback",
            False,
            "settings:/popcorn/ux/soundFeedbackStatus",
            "bool_",
            False,
        ),
        (
            "set_voice_enhancement",
            True,
            "settings:/popcorn/audio/voiceEnhancement",
            "bool_",
            True,
        ),
        (
            "set_codec_led_brightness",
            40,
            "ui:/settings/interface/codecLedBrightness",
            "i32_",
            40,
        ),
        (
            "set_logo_brightness",
            40,
            "ui:/settings/interface/ambeoSection/brightness",
            "i32_",
            40,
        ),
        ("change_logo_state", False, "settings:/popcorn/ui/ledStatus", "bool_", False),
        (
            "set_led_bar_brightness",
            40,
            "ui:/settings/interface/ledBrightness",
            "i32_",
            40,
        ),
        ("set_subwoofer_status", True, "ui:/settings/subwoofer/enabled", "bool_", True),
        # The Plus expects a double subwoofer volume.
        (
            "set_subwoofer_volume",
            -2.5,
            "ui:/settings/subwoofer/volume",
            "double_",
            -2.5,
        ),
        (
            "set_center_volume",
            1.0,
            "settings:/popcorn/audio/centerVolume",
            "double_",
            1.0,
        ),
    ],
)
async def test_popcorn_set_value(method, arg, path, data_type, value):
    """Write each Plus/Mini setting to its device path."""
    bar, transport = _make(AmbeoPopcorn)
    await getattr(bar, method)(arg)
    transport.set_value.assert_awaited_once_with(path, data_type, value)


@pytest.mark.parametrize(
    ("cls", "method", "args", "path", "payload"),
    [
        (AmbeoPopcorn, "set_source", ("hdmi1",), "ui:/inputs/hdmi1", PRESS),
        (AmbeoPopcorn, "play", (), "popcorn:multiPurposeButtonActivate", PRESS),
        (AmbeoPopcorn, "pause", (), "popcorn:multiPurposeButtonActivate", PRESS),
        (
            AmbeoPopcorn,
            "set_bluetooth_pairing_state",
            (True,),
            "bluetooth:deviceList/discoverable",
            PRESS,
        ),
        (AmbeoEspresso, "play", (), "player:player/control", {"control": "play"}),
        (AmbeoEspresso, "pause", (), "player:player/control", {"control": "pause"}),
        (AmbeoEspresso, "next", (), "player:player/control", {"control": "next"}),
        (AmbeoEspresso, "reboot", (), "ui:/settings/system/restart", PRESS),
        (
            AmbeoEspresso,
            "reset_expert_settings",
            (),
            "ui:/settings/audio/resetExpertSettings",
            PRESS,
        ),
    ],
)
async def test_activate(cls, method, args, path, payload):
    """Trigger action paths with the right payload."""
    bar, transport = _make(cls)
    await getattr(bar, method)(*args)
    transport.activate.assert_awaited_once_with(path, payload)
    transport.set_value.assert_not_awaited()


@pytest.mark.parametrize("method", ["stand_by", "wake", "reset_expert_settings"])
async def test_popcorn_unsupported(method):
    """Reject commands the Plus/Mini does not support."""
    bar, _ = _make(AmbeoPopcorn)
    with pytest.raises(NotImplementedError):
        await getattr(bar, method)()


@pytest.mark.parametrize(
    ("subwoofers", "expected"),
    [([{"id": "sub1"}], True), ([], False), (AmbeoResponseError("404", 404), False)],
)
async def test_popcorn_has_subwoofer(subwoofers, expected):
    """Detect a subwoofer from the paired list, once."""
    bar, transport = _make(AmbeoPopcorn)
    transport.get_value = AsyncMock(side_effect=[subwoofers])
    assert await bar.has_subwoofer() is expected
    assert await bar.has_subwoofer() is expected
    transport.get_value.assert_awaited_once_with(
        "settings:/popcorn/subwoofer/list", "popcornSubwooferList"
    )


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"modifiable": True}, True),
        ({"modifiable": False}, False),
        (AmbeoResponseError("404", 404), False),
    ],
)
async def test_espresso_has_subwoofer(data, expected):
    """Detect a subwoofer from the settings path, once."""
    bar, transport = _make(AmbeoEspresso)
    transport.get_data = AsyncMock(side_effect=[data])
    assert await bar.has_subwoofer() is expected
    assert await bar.has_subwoofer() is expected
    transport.get_data.assert_awaited_once_with("ui:/settings/subwoofer/enabled")
