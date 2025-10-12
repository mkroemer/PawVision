"""Playback engine for video process management and timeout control."""

import logging
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional

from .backends import detect_player_backend, PlayerBackend


logger = logging.getLogger(__name__)


class PlaybackEngine:
    """Manages video playback process, timeout, and cleanup."""

    def __init__(self):
        """Initialize the playback engine."""
        self.current_process: Optional[subprocess.Popen] = None
        self.current_video_path: Optional[str] = None
        self.video_start_time: Optional[datetime] = None
        self.timeout_thread: Optional[threading.Thread] = None
        self.process_lock = threading.Lock()
        
        # Detect available player backend
        self.backend: Optional[PlayerBackend] = detect_player_backend()
        if not self.backend:
            logger.warning("No video player backend available")

    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        with self.process_lock:
            return self.current_process is not None and self.current_process.poll() is None

    def start_playback(
        self,
        video_path: str,
        start_time: float,
        volume: int,
        duration: Optional[float] = None,
        on_complete=None,
        on_timeout=None,
    ) -> bool:
        """Start video playback.
        
        Args:
            video_path: Path or URL to video
            start_time: Start position in seconds
            volume: Volume level (0-100)
            duration: Optional playback duration (for timeout)
            on_complete: Optional callback when playback completes
            on_timeout: Optional callback when playback times out
            
        Returns:
            True if playback started successfully
        """
        if not self.backend:
            logger.error("Cannot start playback: no player backend available")
            return False

        try:
            with self.process_lock:
                # Stop any existing playback
                if self.is_playing():
                    self._stop_playback_internal()

                # Start new playback
                self.current_process = self.backend.start_playback(
                    video_path=video_path,
                    start_time=start_time,
                    volume=volume,
                )

                if not self.current_process:
                    logger.error("Backend failed to start playback")
                    return False

                self.current_video_path = video_path
                self.video_start_time = datetime.now()

            # Start timeout thread if duration specified
            if duration:
                self.timeout_thread = threading.Thread(
                    target=self._timeout_handler,
                    args=(duration, on_timeout),
                    daemon=True,
                )
                self.timeout_thread.start()

            logger.info("Video playback started successfully")
            return True

        except OSError as e:
            logger.error("Error starting video playback: %s", e)
            return False

    def stop_playback(self, reason: str = "manual") -> Optional[float]:
        """Stop currently playing video.
        
        Args:
            reason: Reason for stopping (for logging/stats)
            
        Returns:
            Viewing duration in seconds, or None if nothing was playing
        """
        with self.process_lock:
            return self._stop_playback_internal(reason)

    def _stop_playback_internal(self, reason: str = "manual") -> Optional[float]:
        """Internal stop method (assumes lock is held)."""
        if not self.current_process or self.current_process.poll() is not None:
            return None

        logger.info("Stopping video playback (reason: %s)", reason)

        # Calculate viewing duration
        viewing_duration = None
        if self.video_start_time:
            viewing_duration = (datetime.now() - self.video_start_time).total_seconds()

        # Terminate process
        self.current_process.terminate()
        try:
            self.current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Video process did not terminate, killing")
            self.current_process.kill()

        # Clear state
        self.current_process = None
        self.current_video_path = None
        self.video_start_time = None

        return viewing_duration

    def _timeout_handler(self, timeout_sec: float, callback=None):
        """Handle playback timeout.
        
        Args:
            timeout_sec: Timeout duration in seconds
            callback: Optional callback to call when timeout occurs
        """
        time.sleep(timeout_sec)

        with self.process_lock:
            if self.current_process and self.current_process.poll() is None:
                logger.info("Video timeout reached, stopping playback")
                viewing_duration = self._stop_playback_internal("timeout")
                
                # Call callback if provided
                if callback and viewing_duration:
                    try:
                        callback(self.current_video_path, viewing_duration)
                    except Exception as e:
                        logger.error("Error in timeout callback: %s", e)

    def get_current_video_path(self) -> Optional[str]:
        """Get the path of the currently playing video."""
        with self.process_lock:
            return self.current_video_path

    def get_playback_time(self) -> Optional[float]:
        """Get the current playback time in seconds."""
        with self.process_lock:
            if self.video_start_time and self.is_playing():
                return (datetime.now() - self.video_start_time).total_seconds()
            return None

    def cleanup(self):
        """Clean up playback resources."""
        logger.info("Cleaning up playback engine")
        with self.process_lock:
            if self.current_process and self.current_process.poll() is None:
                logger.info("Terminating video process")
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=5)
                except (subprocess.TimeoutExpired, OSError):
                    pass
            self.current_process = None
            self.current_video_path = None
            self.video_start_time = None
