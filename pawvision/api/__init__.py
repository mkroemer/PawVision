"""API blueprints for PawVision web interface."""

from . import video_routes
from . import youtube_routes
from . import playback_routes
from . import config_routes
from . import statistics_routes
from . import dev_routes

__all__ = [
    'video_routes',
    'youtube_routes',
    'playback_routes',
    'config_routes',
    'statistics_routes',
    'dev_routes',
]
