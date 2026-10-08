"""Constants for Ambeo Soundbar API."""

from enum import StrEnum
from typing import NamedTuple

DEFAULT_PORT = 80
DEFAULT_TIMEOUT = 5

# ESPRESSO: MAX
MAX_SOUNDBAR = "AMBEO Soundbar Max"
EXCLUDE_SOURCES_MAX = ["aes"]
AMBEO_MAX_VOLUME_STEP = 0.02


# POPCORN: PLUS/MINI
PLUS_SOUNDBAR = "AMBEO Soundbar Plus"
MINI_SOUNDBAR = "AMBEO Soundbar Mini"
AMBEO_POPCORN_VOLUME_STEP = 0.01


BRIGHTNESS_RANGE_DEFAULT = (0, 100)
BRIGHTNESS_RANGE_AMBEO_MAX_DISPLAY = (1, 126)
BRIGHTNESS_RANGE_AMBEO_MAX_LOGO = (1, 118)


class Capability(StrEnum):
    """Device capability identifiers."""

    AMBEO_LOGO = "AmbeoLogo"
    DECODER_STATUS = "DecoderStatus"
    AMBEO_MODE_LEVEL = "AmbeoModeLevel"
    BLUETOOTH_PAIRING = "AmbeoBluetoothPairing"
    CENTER_SPEAKER_LEVEL = "CenterSpeakerLevel"
    CENTER_VOLUME = "CenterVolume"
    CODEC_LED = "CodecLED"
    ECO_MODE = "EcoMode"
    LED_BAR = "LEDBar"
    MAX_DISPLAY = "AmbeoMaxDisplay"
    MAX_LOGO = "AmbeoMaxLogo"
    RESET_EXPERT_SETTINGS = "ResetExpertSettings"
    SIDE_FIRING_LEVEL = "SideFiringLevel"
    STANDBY = "standby"
    SUBWOOFER = "SubWoofer"
    UP_FIRING_LEVEL = "UpFiringLevel"
    NATIVE_VOLUME = "NativeVolume"
    VOICE_ENHANCEMENT_LEVEL = "VoiceEnhancementLevel"
    VOICE_ENHANCEMENT_TOGGLE = "VoiceEnhancementMode"


class StateKey(StrEnum):
    """Keys of the device state returned by fetch_state() and listen()."""

    VOLUME = "volume"
    MUTED = "muted"
    STATE = "state"
    CURRENT_SOURCE = "current_source"
    CURRENT_PRESET = "current_preset"
    PLAYER_DATA = "player_data"
    PLAY_TIME = "play_time"
    LED_BAR_BRIGHTNESS = "led_bar_brightness"
    CODEC_LED_BRIGHTNESS = "codec_led_brightness"
    LOGO_BRIGHTNESS = "logo_brightness"
    LOGO_STATE = "logo_state"
    DISPLAY_BRIGHTNESS = "display_brightness"
    NIGHT_MODE = "night_mode"
    AMBEO_MODE = "ambeo_mode"
    AMBEO_MODE_LEVEL = "ambeo_mode_level"
    SOUND_FEEDBACK = "sound_feedback"
    VOICE_ENHANCEMENT = "voice_enhancement"
    VOICE_ENHANCEMENT_LEVEL = "voice_enhancement_level"
    BLUETOOTH_PAIRING = "bluetooth_pairing"
    SUBWOOFER_STATUS = "subwoofer_status"
    SUBWOOFER_VOLUME = "subwoofer_volume"
    CENTER_SPEAKER_LEVEL = "center_speaker_level"
    SIDE_FIRING_LEVEL = "side_firing_level"
    UP_FIRING_LEVEL = "up_firing_level"
    CENTER_VOLUME = "center_volume"
    ECO_MODE = "eco_mode"
    DECODER_STATUS = "decoder_status"


class PathSub(NamedTuple):
    """Describes a single event-queue subscription.

    path       -- Device API path to subscribe to.
    data_key   -- Key used in the state dict.
    type_key   -- JSON type key inside the event's itemValue dict.
    capability -- Required device capability, or None if always subscribed.
    sub_key    -- If set, the final value is item_value[type_key][sub_key]
                  (used when the type value is itself a dict).
    """

    path: str
    data_key: StateKey
    type_key: str
    capability: Capability | None = None
    sub_key: str | None = None


class FeatureDef(NamedTuple):
    """Optional state value fetched by fetch_state() when the capability matches."""

    data_key: StateKey
    api_method: str
    capability: Capability | None = None


OPTIONAL_FEATURES: tuple[FeatureDef, ...] = (
    FeatureDef(StateKey.PLAY_TIME, "get_play_time"),
    FeatureDef(
        StateKey.LED_BAR_BRIGHTNESS, "get_led_bar_brightness", Capability.LED_BAR
    ),
    FeatureDef(
        StateKey.CODEC_LED_BRIGHTNESS, "get_codec_led_brightness", Capability.CODEC_LED
    ),
    FeatureDef(StateKey.LOGO_BRIGHTNESS, "get_logo_brightness", Capability.AMBEO_LOGO),
    FeatureDef(StateKey.LOGO_STATE, "get_logo_state", Capability.AMBEO_LOGO),
    FeatureDef(StateKey.NIGHT_MODE, "get_night_mode"),
    FeatureDef(StateKey.AMBEO_MODE, "get_ambeo_mode"),
    FeatureDef(StateKey.SOUND_FEEDBACK, "get_sound_feedback"),
    FeatureDef(
        StateKey.VOICE_ENHANCEMENT,
        "get_voice_enhancement",
        Capability.VOICE_ENHANCEMENT_TOGGLE,
    ),
    FeatureDef(
        StateKey.BLUETOOTH_PAIRING,
        "get_bluetooth_pairing_state",
        Capability.BLUETOOTH_PAIRING,
    ),
    FeatureDef(StateKey.SUBWOOFER_STATUS, "get_subwoofer_status", Capability.SUBWOOFER),
    FeatureDef(StateKey.SUBWOOFER_VOLUME, "get_subwoofer_volume", Capability.SUBWOOFER),
    FeatureDef(
        StateKey.VOICE_ENHANCEMENT_LEVEL,
        "get_voice_enhancement_level",
        Capability.VOICE_ENHANCEMENT_LEVEL,
    ),
    FeatureDef(
        StateKey.CENTER_SPEAKER_LEVEL,
        "get_center_speaker_level",
        Capability.CENTER_SPEAKER_LEVEL,
    ),
    FeatureDef(
        StateKey.SIDE_FIRING_LEVEL,
        "get_side_firing_level",
        Capability.SIDE_FIRING_LEVEL,
    ),
    FeatureDef(
        StateKey.UP_FIRING_LEVEL, "get_up_firing_level", Capability.UP_FIRING_LEVEL
    ),
    FeatureDef(StateKey.CENTER_VOLUME, "get_center_volume", Capability.CENTER_VOLUME),
    FeatureDef(StateKey.ECO_MODE, "get_eco_mode", Capability.ECO_MODE),
    FeatureDef(
        StateKey.DECODER_STATUS, "get_decoder_status", Capability.DECODER_STATUS
    ),
    FeatureDef(
        StateKey.AMBEO_MODE_LEVEL, "get_ambeo_mode_level", Capability.AMBEO_MODE_LEVEL
    ),
)
