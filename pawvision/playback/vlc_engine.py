"""VLC-based playback backend with pause/resume support."""

import logging
import threading
import time
from datetime import datetime
from typing import Optional, Callable
import vlc

logger = logging.getLogger(__name__)


class VLCPlaybackEngine:
    """Manages video playback using python-vlc with full control support."""

    def __init__(self):
        """Initialize the VLC playback engine."""
        self.instance: Optional[vlc.Instance] = None
        self.player: Optional[vlc.MediaPlayer] = None
        self.current_video_path: Optional[str] = None
        self.video_start_time: Optional[datetime] = None
        self.timeout_thread: Optional[threading.Thread] = None
        self.timeout_cancel_event: Optional[threading.Event] = None
        self.position_lock = threading.Lock()
        self.is_paused = False
        self.playback_start_position = 0.0  # Start position in seconds
        
        # Callbacks
        self.on_complete_callback: Optional[Callable] = None
        self.on_timeout_callback: Optional[Callable] = None
        
        
        # Initialize VLC instance
        try:
            self.instance = vlc.Instance('--no-video-title-show', '--quiet')
            logger.info("VLC instance created successfully")
        except Exception as e:
            logger.error("Failed to create VLC instance: %s", e)
            self.instance = None

    def is_playing(self) -> bool:
        """Check if video is currently playing (not paused, not stopped)."""
        with self.position_lock:
            if not self.player:
                return False
            state = self.player.get_state()
            # Treat buffering/opening/paused as active playback to keep status accurate
            return state in (
                vlc.State.Playing,
                vlc.State.Opening,
                vlc.State.Buffering,
                vlc.State.Paused,
            )

    def is_paused_state(self) -> bool:
        """Check if video is paused."""
        with self.position_lock:
            if not self.player:
                return False
            return self.player.get_state() == vlc.State.Paused

    def start_playback(
        self,
        video_path: str,
        start_time: float = 0.0,
        volume: int = 100,
        duration: Optional[float] = None,
        on_complete: Optional[Callable] = None,
        on_timeout: Optional[Callable] = None,
    ) -> bool:
        """Start video playback with VLC.
        
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
        if not self.instance:
            logger.error("Cannot start playback: VLC instance not available")
            return False

        try:
            with self.position_lock:
                # Stop any existing playback and cancel outstanding timers
                if self.player:
                    self._stop_playback_internal("replaced")
                self._cancel_timeout_locked()

                # Create media and player
                media = self.instance.media_new(video_path)
                if not media:
                    logger.error("Failed to create media for: %s", video_path)
                    return False

                self.player = self.instance.media_player_new()
                self.player.set_media(media)
                
                # Set volume (0-100)
                self.player.audio_set_volume(volume)
                
                # Store callbacks
                self.on_complete_callback = on_complete
                self.on_timeout_callback = on_timeout
                
                # Start playback
                self.player.play()
                
                # Wait for player to start
                time.sleep(0.5)
                
                # Seek to start position if specified
                if start_time > 0:
                    # VLC uses milliseconds
                    self.player.set_time(int(start_time * 1000))
                
                self.current_video_path = video_path
                self.video_start_time = datetime.now()
                self.playback_start_position = start_time
                self.is_paused = False

            # Start timeout thread if duration specified
            if duration:
                cancel_event = threading.Event()
                with self.position_lock:
                    self.timeout_cancel_event = cancel_event

                self.timeout_thread = threading.Thread(
                    target=self._timeout_handler,
                    args=(duration, cancel_event),
                    daemon=True,
                )
                self.timeout_thread.start()
            else:
                with self.position_lock:
                    self.timeout_cancel_event = None
                    self.timeout_thread = None

            # Start end-of-playback monitor
            threading.Thread(target=self._monitor_playback_end, daemon=True).start()

            logger.info("VLC playback started successfully")
            return True

        except Exception as e:
            logger.error("Error starting VLC playback: %s", e, exc_info=True)
            return False

    def pause_playback(self) -> bool:
        """Pause the currently playing video."""
        with self.position_lock:
            if not self.player:
                logger.warning("Cannot pause: no player active")
                return False
            
            if self.is_paused:
                logger.info("Video is already paused")
                return True
            
            try:
                self.player.pause()
                self.is_paused = True
                logger.info("Video paused")
                return True
            except Exception as e:
                logger.error("Error pausing playback: %s", e)
                return False

    def resume_playback(self) -> bool:
        """Resume the paused video."""
        with self.position_lock:
            if not self.player:
                logger.warning("Cannot resume: no player active")
                return False
            
            if not self.is_paused:
                logger.info("Video is not paused")
                return True
            
            try:
                self.player.play()
                self.is_paused = False
                logger.info("Video resumed")
                return True
            except Exception as e:
                logger.error("Error resuming playback: %s", e)
                return False

    def stop_playback(self, reason: str = "manual") -> Optional[float]:
        """Stop currently playing video.
        
        Args:
            reason: Reason for stopping (for logging/stats)
            
        Returns:
            Viewing duration in seconds, or None if nothing was playing
        """
        with self.position_lock:
            return self._stop_playback_internal(reason)

    def _cancel_timeout_locked(self):
        """Cancel any outstanding timeout thread. Assumes lock is held."""
        if self.timeout_cancel_event:
            self.timeout_cancel_event.set()
        self.timeout_cancel_event = None
        self.timeout_thread = None

    def _stop_playback_internal(self, reason: str = "manual") -> Optional[float]:
        """Internal stop method (assumes lock is held)."""
        if not self.player:
            return None

        logger.info("Stopping video playback (reason: %s)", reason)

        # Calculate viewing duration
        viewing_duration = None
        if self.video_start_time:
            viewing_duration = (datetime.now() - self.video_start_time).total_seconds()

        # Stop player
        try:
            self.player.stop()
            self.player.release()
        except Exception as e:
            logger.error("Error stopping player: %s", e)

        # Cancel any pending timeout after stopping the player
        self._cancel_timeout_locked()

        # Clear state
        self.player = None
        self.current_video_path = None
        self.video_start_time = None
        self.is_paused = False
        self.playback_start_position = 0.0
        self.on_complete_callback = None
        self.on_timeout_callback = None

        return viewing_duration

    def get_current_position(self) -> Optional[float]:
        """Get current playback position in seconds."""
        with self.position_lock:
            if not self.player:
                return None
            try:
                # VLC returns time in milliseconds
                time_ms = self.player.get_time()
                if time_ms >= 0:
                    return time_ms / 1000.0
                return None
            except Exception as e:
                logger.error("Error getting position: %s", e)
                return None

    def get_playback_time(self) -> Optional[float]:
        """Get the elapsed playback time since start (excludes paused time)."""
        with self.position_lock:
            if not self.player or not self.video_start_time:
                return None
            
            # Get current position in video
            current_pos = self.get_current_position()
            if current_pos is not None:
                # Return time relative to start position
                return current_pos - self.playback_start_position
            
            return None

    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)."""
        with self.position_lock:
            if not self.player:
                return False
            try:
                self.player.audio_set_volume(max(0, min(100, volume)))
                logger.info("Volume set to %d", volume)
                return True
            except Exception as e:
                logger.error("Error setting volume: %s", e)
                return False

    def _timeout_handler(self, timeout_sec: float, cancel_event: threading.Event):
        """Handle playback timeout."""
        if cancel_event.wait(timeout_sec):
            return

        callback = None
        video_path = None
        viewing_duration = None

        with self.position_lock:
            if self.player:
                logger.info("Video timeout reached, stopping playback")
                callback = self.on_timeout_callback
                video_path = self.current_video_path
                viewing_duration = self._stop_playback_internal("timeout")

        if callback and viewing_duration is not None and video_path:
            try:
                callback(video_path, viewing_duration)
            except Exception as e:
                logger.error("Error in timeout callback: %s", e)

    def _monitor_playback_end(self):
        """Monitor for natural end of playback."""
        while True:
            time.sleep(1)

            callback = None
            video_path = None
            viewing_duration = None

            with self.position_lock:
                if not self.player:
                    break

                state = self.player.get_state()
                if state == vlc.State.Ended:
                    logger.info("Video playback ended naturally")
                    callback = self.on_complete_callback
                    video_path = self.current_video_path
                    viewing_duration = self._stop_playback_internal("completed")
                    break

            if callback and viewing_duration is not None and video_path:
                try:
                    callback(video_path, viewing_duration)
                except Exception as e:
                    logger.error("Error in completion callback: %s", e)
                break

    def get_current_video_path(self) -> Optional[str]:
        """Get the path of the currently playing video."""
        with self.position_lock:
            return self.current_video_path

    def cleanup(self):
        """Clean up playback resources."""
        logger.info("Cleaning up VLC playback engine")
        with self.position_lock:
            if self.player:
                try:
                    self.player.stop()
                    self.player.release()
                except Exception:
                    pass
            self.player = None
            self.current_video_path = None
            self.video_start_time = None
            
            if self.instance:
                try:
                    self.instance.release()
                except Exception:
                    pass
                self.instance = None
