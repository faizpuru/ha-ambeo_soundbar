

# Ambeo Soundbar for Home Assistant
[![GitHub Release](https://img.shields.io/github/v/release/faizpuru/ha-ambeo_soundbar?style=flat)](https://github.com/faizpuru/ha-ambeo_soundbar/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

Home Assistant integration to control your Sennheiser AMBEO soundbar directly from your smart home system.

[![Sennheiser](https://raw.githubusercontent.com/home-assistant/brands/refs/heads/master/custom_integrations/ambeo_soundbar/logo.png)](https://www.sennheiser-hearing.com/soundbars/)

## Compatible Devices
- AMBEO Soundbar Max
- AMBEO Soundbar Mini
- AMBEO Soundbar Plus

## Features
### Audio Features

| Feature | Max | Plus | Mini | Description |
|---------|-----|------|------|-------------|
| Night Mode | ✅ | ✅ | ✅ | Reduces dynamic range and bass intensity for quiet listening environments |
| Ambeo Mode | ✅ | ✅ | ✅ | Enables 3D virtualization technology for immersive sound experience |
| Voice Enhancement (Toggle) | ❌ | ✅ | ✅ | On/off toggle to emphasize dialogue frequencies for clearer speech |
| Voice Enhancement (Level) | ✅ | ❌ | ❌ | Adjustable voice enhancement level (0–3) for fine-tuned dialogue clarity |
| Sound Feedback | ✅ | ✅ | ✅ | Enables/disables audio confirmation for user actions |
| Subwoofer Status | ✅ | ✅ | ✅ | Toggles external subwoofer on/off (when connected) |
| Subwoofer Volume | ✅ | ✅ | ✅ | Adjusts subwoofer volume in dB (when connected) |
| Eco Mode | ❌ | ✅ | ✅ | Read-only binary sensor indicating eco mode state |

### Speaker Level Controls (Max only)

| Feature | Max | Plus | Mini | Description |
|---------|-----|------|------|-------------|
| Center Speaker Level | ✅ | ❌ | ❌ | Adjusts center speaker level (-12 to +12 dB) |
| Side Firing Level | ✅ | ❌ | ❌ | Adjusts side-firing speaker level (-12 to +12 dB) |
| Up Firing Level | ✅ | ❌ | ❌ | Adjusts up-firing speaker level (-12 to +12 dB) |

### Sources Management

| Feature | Max | Plus | Mini | Description |
|---------|-----|------|------|-------------|
| Source Selection | ✅ | ✅ | ✅ | Controls input source selection (HDMI, Optical, Bluetooth, etc.) |
| Audio Presets | ✅ | ✅ | ✅ | Sound profiles optimized for different content types |

### Display Controls

| Feature | Max | Plus | Mini | Description |
|---------|-----|------|------|-------------|
| Ambeo Logo | ✅ | ✅ | ✅ | Controls the illuminated Ambeo logo brightness on device |
| LED Bar | ❌ | ✅ | ✅ | Controls front LED display bar brightness for visual feedback |
| Main Display | ✅ | ❌ | ❌ | Controls device's screen brightness and display settings |
| Codec LED | ❌ | ✅ | ✅ | Controls LED indicator showing active audio codec |

### Media Player Controls

| Feature | Max | Plus | Mini | Description |
|---------|-----|------|------|-------------|
| Play/Pause | ✅ | ✅ | ✅ | Controls media playback state |
| Next/Previous | ✅ | ✅ | ✅ | Skip to next or previous track |
| Volume | ✅ | ✅ | ✅ | Adjusts audio volume level |
| Mute | ✅ | ✅ | ✅ | Toggles audio mute state |

### Additional Features

| Feature | Max | Plus | Mini | Description |
|---------|-----|------|------|-------------|
| Bluetooth Pairing | ❌ | ✅ | ✅ | Manages Bluetooth device pairing mode and connected devices |
| Standby Control | ✅ | ❌ | ❌ | Controls device power state between active and standby mode |
| Reset Expert Settings | ✅ | ❌ | ❌ | Resets all audio customization settings to factory defaults |
| Restart | ✅ | ✅ | ✅ | Reboots the device |

## 🚀 Quick Start

### 📦 Using HACS (Recommended)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=faizpuru&repository=ha-ambeo_soundbar&category=integration)

1. Use the button above or search for "Ambeo Soundbar" in HACS
2. Download the integration and restart Home Assistant

### ⚙️ Manual Installation
1. Download the `custom_components/ambeo_soundbar` directory to your Home Assistant configuration directory
2. Restart Home Assistant

## 🔧 Setup
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ambeo_soundbar)

1. Go to the Integrations page in Home Assistant
2. Click "Add Integration" and search for "Ambeo Soundbar"
3. Enter your soundbar's IP address
4. Integration will be ready within a few seconds

## ⚙️ Configuration

### Initial Setup

| Option | Default | Description |
|--------|---------|-------------|
| Host | `ambeo.local` | IP address or hostname of the soundbar |
| Update Interval | `10` | Polling interval in seconds |

### Options (after setup)

These settings can be changed at any time via **Settings > Devices & Services > Ambeo Soundbar > Configure**.

| Option | Default | Description |
|--------|---------|-------------|
| Host | — | Change the soundbar IP address (validated on save) |
| Update Interval | `10` | Polling interval in seconds |
| Debounce Cooldown | `0` | *Max only* — Experimental: cooldown in seconds to prevent API flooding during rapid commands. Set to `0` to disable |

## ❓ Troubleshooting

If you encounter any issues:
1. Verify that your soundbar is powered on and connected to your network
2. Double-check that the configured IP address is correct
3. Check Home Assistant logs for any error details


## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest improvements
- 🔀 Submit pull requests

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This project is a community development and is not affiliated with or endorsed by Sennheiser. All product names, logos, and brands are property of their respective owners.

---

If you find this integration helpful, please consider giving it a ⭐️ on GitHub!
