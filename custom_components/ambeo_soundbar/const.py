DOMAIN = "ambeo_soundbar"
VERSION = "1.0.0"
MANUFACTURER = "Sennheiser"
DEFAULT_PORT = 80

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

POPCORN_API_MODELS = [PLUS_SOUNDBAR, MINI_SOUNDBAR]
ESPRESSO_API_MODELS = [MAX_SOUNDBAR]


class Capability:
    AMBEO_LOGO = "AmbeoLogo"
    LED_BAR = "LEDBar"
    CODEC_LED = "CodecLED"
    VOICE_ENHANCEMENT = "VoiceEnhancementMode"
    BLUETOOTH_PAIRING = "AmbeoBluetoothPairing"
    SUBWOOFER = "SubWoofer"
    STANDBY = "standby"
    MAX_LOGO = "AmbeoMaxLogo"
    MAX_DISPLAY = "AmbeoMaxDisplay"
