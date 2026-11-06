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
| Product picture (diagnostic image) | ❓ | ✅ | ❓ |
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

## Use cases

- Turn Night Mode on in the evening, so dialogue stays clear without waking the house.
- Switch the soundbar to the TV input and the Movie sound mode when the TV turns on.
- Pause playback or lower the volume when the doorbell rings or a call comes in.
- Control volume, mute, source and playback from dashboards and voice assistants, like any media player.
- Keep an eye on the incoming audio format with the Audio Codec and Decoder Status sensors.

## Examples

Replace `living_room` with the name of your soundbar in the entity IDs. Source and sound mode names are the ones of your soundbar, as listed by its media player (for instance `HDMI TV`, `Optical`, `Movie` or `Music`). Renamed inputs appear under their custom name.

### Night Mode in the evening

```yaml
automation:
  - alias: "Soundbar night mode"
    triggers:
      - trigger: time
        at: "21:30:00"
        id: "on"
      - trigger: time
        at: "08:00:00"
        id: "off"
    actions:
      - action: "switch.turn_{{ trigger.id }}"
        target:
          entity_id: switch.living_room_night_mode
```

### Follow the TV

```yaml
automation:
  - alias: "Soundbar follows the TV"
    triggers:
      - trigger: state
        entity_id: media_player.tv
        to: "on"
    actions:
      - action: media_player.select_source
        target:
          entity_id: media_player.living_room
        data:
          source: "HDMI TV"
      - action: media_player.select_sound_mode
        target:
          entity_id: media_player.living_room
        data:
          sound_mode: "Movie"
```

### Pause when the doorbell rings

```yaml
automation:
  - alias: "Pause the soundbar on doorbell"
    triggers:
      - trigger: state
        entity_id: binary_sensor.doorbell
        to: "on"
    actions:
      - action: media_player.media_pause
        target:
          entity_id: media_player.living_room
```

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

## Data updates

The integration talks to the soundbar over its local HTTP API, without any cloud service.

- The soundbar pushes its changes (volume, mute, source, playback, settings) as they happen, including those made with the remote or the Sennheiser app.
- On top of that, every setting is polled at the update interval (30 s by default, see [Configuration](#configuration)), to catch anything the pushed changes miss.
- Changes made from Home Assistant show up right away, then are confirmed by the soundbar.
- The product picture is read once at startup, from the soundbar itself, and never refreshed.
- When the soundbar cannot be reached, its entities become unavailable until it answers again.

## Known limitations

- AirPlay and Google Cast show up as the source while in use, but cannot be selected: start the stream from your phone or app.
- Next, previous, seek, shuffle and repeat only show up when the current stream supports them, so not on HDMI, optical or AUX.
- Inputs renamed on the soundbar keep their old name in Home Assistant until the integration is reloaded.
- Ambeo Max: the display shows half of the volume (0–50) while the media player uses 0–100 %. The **Volume (native)** entity follows the display scale.
- Only the settings listed in [Features](#features) are available. Other settings of the Sennheiser app (lip sync, Dolby options, firmware updates…) are not exposed yet.
- Automatic discovery is confirmed on the Plus. If a Max or Mini does not show up, add it by host.
- After an IP address change, discovery can take a few minutes: the soundbar does not always answer network queries that ask for many services at once. Use **Reconfigure** to update the host right away.

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
