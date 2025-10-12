"""Video player backends (MPV, VLC, OMXPlayer)."""

import logging
import subprocess
from abc import ABC, abstractmethod
from typing import Optional


logger = logging.getLogger(__name__)


class PlayerBackend(ABC):
    """Abstract base class for video player backends."""

    @abstractmethod
    def start_playback(
        self,
        video_path: str,
        start_time: float,
        volume: int,
        **kwargs
    ) -> Optional[subprocess.Popen]:
        """Start video playback.
        
        Args:
            video_path: Path or URL to video
            start_time: Start position in seconds
            volume: Volume level (0-100)
            **kwargs: Additional backend-specific options
            
        Returns:
            subprocess.Popen object, or None if failed
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on the system."""
        pass


class MPVBackend(PlayerBackend):
    """MPV video player backend."""

    def is_available(self) -> bool:
        """Check if MPV is available."""
        try:
            result = subprocess.run(
                ["mpv", "--version"],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, OSError):
            return False

    def start_playback(
        self,
        video_path: str,
        start_time: float,
        volume: int,
        **kwargs
    ) -> Optional[subprocess.Popen]:
        """Start video playback with MPV."""
        try:
            cmd = [
                "mpv",
                f"--start={start_time}",
                f"--volume={volume}",
                "--really-quiet",  # Reduce mpv output
                video_path,
            ]
            
            logger.debug("Starting MPV with command: %s", " ".join(cmd))
            return subprocess.Popen(cmd)
            
        except OSError as e:
            logger.error("Error starting MPV playback: %s", e)
            return None


class VLCBackend(PlayerBackend):
    """VLC video player backend."""

    def is_available(self) -> bool:
        """Check if VLC is available."""
        try:
            result = subprocess.run(
                ["vlc", "--version"],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, OSError):
            return False

    def start_playback(
        self,
        video_path: str,
        start_time: float,
        volume: int,
        **kwargs
    ) -> Optional[subprocess.Popen]:
        """Start video playback with VLC."""
        try:
            # VLC volume is 0-256 (256 = 100%)
            vlc_volume = int((volume / 100.0) * 256)
            
            cmd = [
                "vlc",
                "--play-and-exit",  # Exit after playback
                "--no-video-title-show",  # Don't show filename
                f"--start-time={int(start_time)}",
                f"--volume={vlc_volume}",
                video_path,
            ]
            
            logger.debug("Starting VLC with command: %s", " ".join(cmd))
            return subprocess.Popen(cmd)
            
        except OSError as e:
            logger.error("Error starting VLC playback: %s", e)
            return None


class OMXPlayerBackend(PlayerBackend):
    """OMXPlayer backend (legacy Raspberry Pi player)."""

    def is_available(self) -> bool:
        """Check if OMXPlayer is available."""
        try:
            result = subprocess.run(
                ["omxplayer", "--version"],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, OSError):
            return False

    def start_playback(
        self,
        video_path: str,
        start_time: float,
        volume: int,
        **kwargs
    ) -> Optional[subprocess.Popen]:
        """Start video playback with OMXPlayer."""
        try:
            # OMXPlayer volume is in millibels (mB)
            # 0 mB = 100%, -6000 mB = 0%
            # Convert from 0-100 to millibels
            if volume == 0:
                omx_volume = -6000
            else:
                omx_volume = int(-6000 + (volume / 100.0) * 6000)
            
            cmd = [
                "omxplayer",
                "--no-osd",  # No on-screen display
                f"--pos={int(start_time)}",
                f"--vol={omx_volume}",
                video_path,
            ]
            
            logger.debug("Starting OMXPlayer with command: %s", " ".join(cmd))
            return subprocess.Popen(cmd)
            
        except OSError as e:
            logger.error("Error starting OMXPlayer playback: %s", e)
            return None


def detect_player_backend() -> Optional[PlayerBackend]:
    """Detect and return the first available player backend.
    
    Tries backends in order: MPV, VLC, OMXPlayer
    
    Returns:
        First available PlayerBackend instance, or None if none available
    """
    backends = [MPVBackend(), VLCBackend(), OMXPlayerBackend()]
    
    for backend in backends:
        if backend.is_available():
            backend_name = backend.__class__.__name__
            logger.info("Detected available player backend: %s", backend_name)
            return backend
    
    logger.error("No video player backend available (tried: MPV, VLC, OMXPlayer)")
    return None
