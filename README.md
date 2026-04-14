# Ambeo Soundbar for Home Assistant
[![GitHub Release](https://img.shields.io/github/v/release/faizpuru/ha-ambeo_soundbar?style=flat)](https://github.com/faizpuru/ha-ambeo_soundbar/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

The **Sennheiser AMBEO Soundbar** is a premium home audio device featuring 3D spatial sound. The AMBEO line includes the Max, Plus, and Mini models.

This integration brings full local control of your AMBEO soundbar into Home Assistant over your local network, with no cloud dependency. It exposes the soundbar as a media player along with dedicated entities for all audio, display, and connectivity settings.

[![Sennheiser](https://raw.githubusercontent.com/home-assistant/brands/refs/heads/master/custom_integrations/ambeo_soundbar/logo.png)](https://www.sennheiser-hearing.com/soundbars/)

## Supported Devices

- AMBEO Soundbar Max
- AMBEO Soundbar Plus
- AMBEO Soundbar Mini

## Features

| Feature | Max | Plus | Mini |
|---------|:---:|:----:|:----:|
| Media player (play/pause, volume, source, preset) | ✅ | ✅ | ✅ |
| Night Mode | ✅ | ✅ | ✅ |
| Ambeo Mode | ✅ | ✅ | ✅ |
| Sound Feedback | ✅ | ✅ | ✅ |
| Subwoofer (status + volume) | ✅ | ✅ | ✅ |
| Ambeo Logo brightness | ✅ | ✅ | ✅ |
| Restart | ✅ | ✅ | ✅ |
| Voice Enhancement toggle | ❌ | ✅ | ✅ |
| LED Bar + Codec LED brightness | ❌ | ✅ | ✅ |
| Bluetooth Pairing | ❌ | ✅ | ✅ |
| Eco Mode (read-only) | ❌ | ✅ | ✅ |
| Voice Enhancement level (0–3) | ✅ | ❌ | ❌ |
| Speaker Levels (center, side, up-firing) | ✅ | ❌ | ❌ |
| Display + Logo brightness | ✅ | ❌ | ❌ |
| Standby control | ✅ | ❌ | ❌ |
| Reset Expert Settings | ✅ | ❌ | ❌ |

## Actions

This integration uses standard Home Assistant platforms — no custom services. Available actions per platform:

- **`media_player`**: `volume_set`, `volume_mute`, `select_source`, `select_sound_mode`, `media_play/pause`, `media_next/previous_track`, `turn_on/off`
- **`switch`**: `turn_on/off` (Night Mode, Ambeo Mode, Sound Feedback, Voice Enhancement, Subwoofer, Bluetooth Pairing)
- **`number`**: `set_value` (Subwoofer Volume, Voice Enhancement Level, Speaker Levels, Native Volume)
- **`light`**: `turn_on/off` (LED brightness controls)
- **`button`**: `press` (Restart, Reset Expert Settings)

## Installation

**Prerequisites:** Home Assistant 2024.1+, soundbar and HA on the same local network.

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=faizpuru&repository=ha-ambeo_soundbar&category=integration)

Search for **"Ambeo Soundbar"** in HACS, download, then restart Home Assistant.

### Manual

Copy the `custom_components/ambeo_soundbar` folder into your HA config directory, then restart.

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ambeo_soundbar)

Go to **Settings > Devices & Services > Add Integration**, search for "Ambeo Soundbar", and enter the soundbar's IP address or hostname (default: `ambeo.local`).

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| Host | `ambeo.local` | IP address or hostname |
| Update Interval | `10s` | Polling interval |
| Debounce Cooldown | `0` | Max only — experimental idle-state delay (seconds) |

Options can be changed anytime via **Settings > Devices & Services > Ambeo Soundbar > Configure**.

## Removal

Go to **Settings > Devices & Services**, find **Ambeo Soundbar**, open the three-dot menu and select **Delete**.

## Troubleshooting

- Verify the soundbar is powered on and reachable on the network
- Confirm the configured IP address is correct
- Check Home Assistant logs for error details

## Contributing

Bug reports, feature requests and pull requests are welcome — open an issue or PR on [GitHub](https://github.com/faizpuru/ha-ambeo_soundbar).

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This project is a community effort and is not affiliated with or endorsed by Sennheiser.

---

If this integration is useful to you, consider giving it a ⭐ on [GitHub](https://github.com/faizpuru/ha-ambeo_soundbar)!
