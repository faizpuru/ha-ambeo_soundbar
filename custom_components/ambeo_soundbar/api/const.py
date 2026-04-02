"""Constants for Ambeo Soundbar API."""

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
    BLUETOOTH_PAIRING = "AmbeoBluetoothPairing"
    CENTER_SPEAKER_LEVEL = "CenterSpeakerLevel"
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
    VOICE_ENHANCEMENT_LEVEL = "VoiceEnhancementLevel"
    VOICE_ENHANCEMENT_TOGGLE = "VoiceEnhancementMode"
