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
| Ambeo Mode (on/off switch) | ✅ | ✅ | ✅ |
| Ambeo Mode Level (Off/Light/Regular/Boost) | ✅ | ❌ | ❌ |
| Sound Feedback | ✅ | ✅ | ✅ |
| Subwoofer (status + volume) | ✅ | ✅ | ✅ |
| Ambeo Logo brightness | ✅ | ✅ | ✅ |
| Restart | ✅ | ✅ | ✅ |
| Decoder Status (diagnostic sensor) | ✅ | ✅ | ✅ |
| Audio Codec (diagnostic sensor) | ❓ | ✅ | ✅ |
| Voice Enhancement toggle | ❌ | ✅ | ✅ |
| LED Bar + Codec LED brightness | ❌ | ✅ | ✅ |
| Bluetooth Pairing | ❌ | ✅ | ✅ |
| Eco Mode (read-only) | ❌ | ✅ | ✅ |
| Center Volume | ❌ | ✅ | ✅ |
| Voice Enhancement level (0–3) | ✅ | ❌ | ❌ |
| Speaker Levels (center, side, up-firing) | ✅ | ❌ | ❌ |
| Display + Logo brightness | ✅ | ❌ | ❌ |
| Standby control | ✅ | ❌ | ❌ |
| Reset Expert Settings | ✅ | ❌ | ❌ |

## Actions

This integration uses standard Home Assistant platforms — no custom services. Available actions per platform:

- **`media_player`**: `volume_set`, `volume_mute`, `select_source`, `select_sound_mode`, `media_play/pause`, `media_next/previous_track`, `turn_on/off`
- **`switch`**: `turn_on/off` (Night Mode, Ambeo Mode, Sound Feedback, Voice Enhancement, Subwoofer, Bluetooth Pairing)
- **`select`**: `select_option` (Ambeo Mode Level: Off/Light/Regular/Boost)
- **`number`**: `set_value` (Subwoofer Volume, Voice Enhancement Level, Speaker Levels, Center Volume, Native Volume)
- **`light`**: `turn_on/off` (LED brightness controls)
- **`button`**: `press` (Restart, Reset Expert Settings)

## Installation

**Prerequisites:** Home Assistant 2024.11+, soundbar and HA on the same local network.

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=faizpuru&repository=ha-ambeo_soundbar&category=integration)

Search for **"Ambeo Soundbar"** in HACS, download, then restart Home Assistant.

### Manual

Copy the `custom_components/ambeo_soundbar` folder into your HA config directory, then restart.

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ambeo_soundbar)

The soundbar is discovered automatically on the local network: it shows up under **Settings > Devices & Services**, where you only have to confirm it.

To add it by hand, go to **Settings > Devices & Services > Add Integration** and search for "Ambeo Soundbar". Setup asks for one parameter:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Host | `ambeo.local` | IP address or hostname of the soundbar. You can find the IP address in your router. |

## Configuration

Go to **Settings > Devices & Services > Ambeo Soundbar > Configure** to change these options at any time:

| Option | Default | Description |
|--------|---------|-------------|
| Update interval | `30` s | How often the soundbar is polled. The soundbar also pushes most changes as they happen. |
| Max concurrent requests | `3` | Maximum number of simultaneous requests sent to the soundbar during a poll. Lower it if the soundbar becomes unresponsive. |

### Changing the host

If the soundbar gets a new IP address, Home Assistant picks it up from discovery. You can also open the three-dot menu of the integration entry and select **Reconfigure**. The new host must answer with the same soundbar.

## Removal

Go to **Settings > Devices & Services**, find **Ambeo Soundbar**, open the three-dot menu and select **Delete**.

## Troubleshooting

- Verify the soundbar is powered on and reachable on the network
- Confirm the configured IP address is correct
- Check Home Assistant logs for error details
- **Unsupported model**: the device answered but is not an AMBEO Soundbar Max, Plus or Mini
- **Different device** (reconfigure): the new host is another soundbar; add it as a new device instead

## Contributing

Bug reports, feature requests and pull requests are welcome — open an issue or PR on [GitHub](https://github.com/faizpuru/ha-ambeo_soundbar).

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This project is a community effort and is not affiliated with or endorsed by Sennheiser.

---

If this integration is useful to you, consider giving it a ⭐ on [GitHub](https://github.com/faizpuru/ha-ambeo_soundbar)!
