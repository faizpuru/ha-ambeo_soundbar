"""Data models for the Ambeo Soundbar API."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Static information about a soundbar."""

    model: str
    name: str | None
    serial: str | None
    firmware_version: str | None


@dataclass(frozen=True, slots=True)
class Source:
    """An audio input (HDMI, Optical, …)."""

    id: str | int
    title: str


@dataclass(frozen=True, slots=True)
class Preset:
    """An audio preset / sound mode (Movies, Music, …)."""

    id: str | int
    title: str


class PlayerStatus(StrEnum):
    """Effective playback status derived from the device state."""

    PLAYING = "playing"
    PAUSED = "paused"
    IDLE = "idle"
    ON = "on"
    STANDBY = "standby"
