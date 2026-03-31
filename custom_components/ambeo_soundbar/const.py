"""Constants for Ambeo Soundbar integration."""
DOMAIN = "ambeo_soundbar"
PLATFORMS = ["binary_sensor", "button", "light", "media_player", "number", "switch"]
VERSION = "1.1.0"
MANUFACTURER = "Sennheiser"
DEFAULT_PORT = 80
TIMEOUT = 5

CONFIG_HOST = "host"
CONFIG_DEBOUNCE_COOLDOWN = "debounce_cooldown"
CONFIG_DEBOUNCE_COOLDOWN_DEFAULT = 0
CONFIG_HOST_DEFAULT = "ambeo.local"
CONFIG_UPDATE_INTERVAL = "update_interval"
CONFIG_UPDATE_INTERVAL_DEFAULT = 10

BRIGHTNESS_SCALE = (0, 100)
DEFAULT_BRIGHTNESS = 50

# ESPRESSO: MAX
MAX_SOUNDBAR = "AMBEO Soundbar Max"
BRIGHTNESS_SCALE_AMBEO_MAX_DISPLAY = (1, 126)
EXCLUDE_SOURCES_MAX = ["aes"]
AMBEO_MAX_VOLUME_STEP = 0.02
DEFAULT_BRIGHTNESS_AMBEO_MAX = 128
BRIGHTNESS_SCALE_AMBEO_MAX_LOGO = (1, 118)

# POPCORN: PLUS/MINI
PLUS_SOUNDBAR = "AMBEO Soundbar Plus"
MINI_SOUNDBAR = "AMBEO Soundbar Mini"
AMBEO_POPCORN_VOLUME_STEP = 0.01

POPCORN_API_MODELS = [MINI_SOUNDBAR, PLUS_SOUNDBAR]
ESPRESSO_API_MODELS = [MAX_SOUNDBAR]


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
