"""Playback module for video player components."""

from .engine import PlaybackEngine
from .video_utils import get_video_duration, format_duration
from .backends import detect_player_backend, MPVBackend

__all__ = [
    "PlaybackEngine",
    "get_video_duration",
    "format_duration",
    "detect_player_backend",
    "MPVBackend",
]
