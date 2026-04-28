"""Constants for Ambeo Soundbar API."""

from typing import NamedTuple


class PathSub(NamedTuple):
    """Describes a single event-queue subscription.

    path       -- Device API path to subscribe to.
    data_key   -- Key used in the coordinator data dict.
    type_key   -- JSON type key inside the event's itemValue dict.
    capability -- Required device capability, or None if always subscribed.
    sub_key    -- If set, the final value is item_value[type_key][sub_key]
                  (used when the type value is itself a dict).
    """

    path: str
    data_key: str
    type_key: str
    capability: str | None = None
    sub_key: str | None = None


# ESPRESSO: MAX
MAX_SOUNDBAR = "AMBEO Soundbar Max"
EXCLUDE_SOURCES_MAX = ["aes"]
AMBEO_MAX_VOLUME_STEP = 0.02


# POPCORN: PLUS/MINI
PLUS_SOUNDBAR = "AMBEO Soundbar Plus"
MINI_SOUNDBAR = "AMBEO Soundbar Mini"
AMBEO_POPCORN_VOLUME_STEP = 0.01

POPCORN_API_MODELS = [MINI_SOUNDBAR, PLUS_SOUNDBAR]
ESPRESSO_API_MODELS = [MAX_SOUNDBAR]


BRIGHTNESS_RANGE_DEFAULT = (0, 100)
BRIGHTNESS_RANGE_AMBEO_MAX_DISPLAY = (1, 126)
BRIGHTNESS_RANGE_AMBEO_MAX_LOGO = (1, 118)


class Capability:
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
