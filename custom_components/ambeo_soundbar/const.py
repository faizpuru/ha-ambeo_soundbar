"""Constants for Ambeo Soundbar integration."""

DOMAIN = "ambeo_soundbar"
PLATFORMS = [
    "binary_sensor",
    "button",
    "light",
    "media_player",
    "number",
    "select",
    "sensor",
    "switch",
]
VERSION = "1.1.0"
MANUFACTURER = "Sennheiser"
DEFAULT_PORT = 80
TIMEOUT = 5

CONFIG_HOST = "host"
CONFIG_DEBOUNCE_COOLDOWN = "debounce_cooldown"
CONFIG_DEBOUNCE_COOLDOWN_DEFAULT = 0
CONFIG_HOST_DEFAULT = "ambeo.local"
CONFIG_UPDATE_INTERVAL = "update_interval"
CONFIG_UPDATE_INTERVAL_DEFAULT = 30
CONFIG_CONCURRENT_REQUESTS = "concurrent_requests"
CONFIG_CONCURRENT_REQUESTS_DEFAULT = 3
