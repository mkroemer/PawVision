"""Video player with proper process management."""

import atexit
import logging
import os
import random
import signal
import threading
from datetime import datetime
from typing import Dict, List, Optional

from .database import VideoEntry
from .playback import PlaybackEngine, format_duration, get_video_duration
from .playback.vlc_engine import VLCPlaybackEngine
from .time_utils import time_parser
from .video_library import VideoLibraryManager


class VideoPlayer:
    """Manages video playback with proper process management."""

    def __init__(self, config, video_dirs, statistics_manager=None, monitor_manager=None):
        """Initialize the video player with configuration and video directories."""
        self.config = config
        self.video_dirs = video_dirs
        self.statistics_manager = statistics_manager
        self.monitor_manager = monitor_manager
        self.process_lock = threading.RLock()  # Use RLock for reentrant locking
        self.last_playback_end = None  # Track when last video ended
        self.motion_detected = False  # Track motion sensor state
        self.current_video = None  # Current video path for statistics
        self.prefer_local_playback = config.prefer_local_playback

        # Initialize VLC playback engine (with fallback to old engine)
        try:
            self.playback_engine = VLCPlaybackEngine()
            self.vlc_enabled = True
            self.logger = logging.getLogger(__name__)
            self.logger.info("Using VLC playback engine with pause/resume support")
        except Exception as e:
            self.logger = logging.getLogger(__name__)
            self.logger.warning("VLC engine not available, falling back to basic playback: %s", e)
            self.playback_engine = PlaybackEngine()
            self.vlc_enabled = False

        # Initialize video library manager
        db_path = getattr(config, "database_path", "pawvision.db")
        youtube_cache_dir = getattr(config, "youtube_cache_dir", "youtube_cache")
        youtube_preferred_quality = getattr(config, "youtube_preferred_quality", "720p")
        self.library_manager = VideoLibraryManager(
            db_path=db_path,
            video_directories=video_dirs,
            youtube_cache_dir=youtube_cache_dir,
            youtube_preferred_quality=youtube_preferred_quality,
        )
        
        self.monitor_relay = None
        self.logger = logging.getLogger(__name__)

        # Initialize monitor control
        self._init_monitor_control()

        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _init_monitor_control(self):
        """Initialize monitor control based on configuration."""
        if self.config.monitor_gpio is not None:
            try:
                # Only import and initialize if not in dev mode
                if hasattr(self.config, "dev_mode") and not getattr(self.config, "dev_mode", False):
                    from gpiozero import OutputDevice

                    self.monitor_relay = OutputDevice(self.config.monitor_gpio)
                    self.logger.info("Monitor relay initialized on GPIO %d", self.config.monitor_gpio)
            except (ImportError, OSError) as e:
                self.logger.error("Error initializing monitor relay: %s", e)

    def _signal_handler(self, signum, _frame):
        """Handle shutdown signals."""
        self.logger.info("Received signal %d, shutting down...", signum)
        self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up video player resources")
        self.playback_engine.cleanup()
        self.turn_monitor_off()

    def sync_video_library(self):
        """Sync the video library with filesystem."""
        video_files = self.get_all_video_files()
        # Create a wrapper function that handles the library manager context
        def duration_getter(path):
            video_entry = self.library_manager.get_video(path)
            return get_video_duration(path, self.library_manager, video_entry)
        
        added, updated, removed = self.library_manager.sync_with_filesystem(video_files, duration_getter)
        if added > 0 or updated > 0 or removed > 0:
            self.logger.info(
                "Video library synced: %d added, %d updated, %d removed",
                added,
                updated,
                removed,
            )

    def _get_playback_path(self, video_entry: VideoEntry) -> Optional[str]:
        """Get the actual path/URL to use for video playback.

        For YouTube videos, this handles:
        - Using downloaded file if available
        - Using cached stream URL if valid
        - Refreshing stream URL if expired
        - Falling back to original YouTube URL
        """
        if not video_entry.is_youtube:
            # For local files, just return the path if it exists
            if os.path.exists(video_entry.path):
                return video_entry.path
            else:
                self.logger.error("Local video file not found: %s", video_entry.path)
                return None

        # Handle YouTube videos - prefer downloaded file, then stream URL, then YouTube URL
        # 1. Check if we have a downloaded file
        if self.prefer_local_playback and video_entry.download_path and os.path.exists(video_entry.download_path):
            self.logger.debug("Using downloaded file for YouTube video: %s", video_entry.download_path)
            return video_entry.download_path

        # 2. Check if we have a valid stream URL
        if video_entry.stream_url and not video_entry.is_stream_expired():
            self.logger.debug("Using cached stream URL for YouTube video")
            return video_entry.stream_url

        # 3. Stream URL is expired or doesn't exist - refresh it
        self.logger.info(
            "Refreshing stream URL for YouTube video: %s",
            video_entry.get_display_title(),
        )

        if self.library_manager.youtube_manager.refresh_stream_url(video_entry):
            # Update the database with new stream URL
            self.library_manager.add_or_update_video(video_entry)
            return video_entry.stream_url
        else:
            self.logger.error(
                "Failed to refresh stream URL for: %s",
                video_entry.get_display_title(),
            )
            # Fall back to original YouTube URL as last resort
            return video_entry.youtube_url

    def get_all_video_files(self) -> List[str]:
        """Get list of all video files in configured directories (filesystem scan)."""
        videos = []
        supported_extensions = (".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm")

        # Get all YouTube download paths to exclude from local scan
        youtube_download_paths = set()
        for entry in self.library_manager.get_all_videos():
            if entry.is_youtube and entry.download_path:
                youtube_download_paths.add(os.path.abspath(entry.download_path))

        for vdir in self.video_dirs:
            if not os.path.exists(vdir):
                self.logger.warning("Video directory does not exist: %s", vdir)
                continue

            try:
                for filename in os.listdir(vdir):
                    if filename.lower().endswith(supported_extensions):
                        full_path = os.path.join(vdir, filename)
                        if os.path.isfile(full_path):
                            # Skip files that are YouTube downloads
                            if os.path.abspath(full_path) not in youtube_download_paths:
                                videos.append(full_path)
            except OSError as e:
                self.logger.error("Error reading video directory %s: %s", vdir, e)

        self.logger.debug("Found %d videos (excluding YouTube downloads)", len(videos))
        return videos

    def get_video_library_entries(self) -> List[VideoEntry]:
        """Get all video entries from the library."""
        # Sync library with filesystem first
        self.sync_video_library()
        return self.library_manager.get_all_videos()

    def get_playable_videos(self) -> List[VideoEntry]:
        """Get videos that are playable (have valid duration range)."""
        # Sync library with filesystem first
        self.sync_video_library()
        return self.library_manager.get_playable_videos()

    def run_housekeeping(self) -> None:
        """Run low-frequency YouTube/thumbnail housekeeping tasks."""
        try:
            max_download_storage_gb = getattr(self.config, "youtube_max_download_storage_gb", None)
            self.library_manager.run_housekeeping(max_download_storage_gb=max_download_storage_gb)
        except Exception as e:
            self.logger.error("Housekeeping run failed: %s", e)

    def get_video_duration(self, file_path: str) -> Optional[float]:
        """Get video duration in seconds using mediainfo with database caching."""
        video_entry = self.library_manager.get_video(file_path)
        return get_video_duration(file_path, self.library_manager, video_entry)

    def is_night_mode(self) -> bool:
        """Check if current time is in night mode."""
        return time_parser.is_time_in_range(self.config.night_mode_start, self.config.night_mode_end)

    def turn_monitor_on(self):
        """Turn monitor on."""
        dev_mode = getattr(self.config, "dev_mode", False)

        if dev_mode:
            self.logger.info("DEV_MODE: Would turn monitor on")
            return

        try:
            if self.monitor_relay:
                self.monitor_relay.on()
                self.logger.info("Monitor turned on via GPIO")
            else:
                import subprocess
                subprocess.run("vcgencmd display_power 1", shell=True, check=False)
                self.logger.info("Monitor turned on via vcgencmd")
        except (AttributeError, OSError) as e:
            self.logger.error("Error turning monitor on: %s", e)

    def turn_monitor_off(self):
        """Turn monitor off."""
        dev_mode = getattr(self.config, "dev_mode", False)

        if dev_mode:
            self.logger.info("DEV_MODE: Would turn monitor off")
            return

        try:
            if self.monitor_relay:
                self.monitor_relay.off()
                self.logger.info("Monitor turned off via GPIO")
            else:
                import subprocess
                subprocess.run("vcgencmd display_power 0", shell=True, check=False)
                self.logger.info("Monitor turned off via vcgencmd")
        except (AttributeError, OSError) as e:
            self.logger.error("Error turning monitor off: %s", e)

    def _handle_playback_finished(self, video_path: Optional[str], viewing_duration: Optional[float], reason: str):
        """Handle common cleanup after the playback engine stops on its own."""
        if viewing_duration is None:
            return

        turn_off_monitor = reason in ("timeout", "completed")

        with self.process_lock:
            if reason in ("manual", "switch", "web"):
                self.last_playback_end = None
            else:
                self.last_playback_end = datetime.now()

            if self.statistics_manager and video_path:
                self.statistics_manager.record_video_viewing(video_path, viewing_duration, reason)

            self.current_video = None

        if turn_off_monitor:
            self.turn_monitor_off()

    def get_current_video_info(self) -> Optional[dict]:
        """Get information about the currently playing video."""
        with self.process_lock:
            if not self.playback_engine.is_playing() or self.current_video is None:
                return None

            # Get video entry information
            video_entry = self.get_video_entry(self.current_video)
            if not video_entry:
                return None

            # Get playback time from engine
            playback_time = self.playback_engine.get_playback_time()

            return {
                "path": video_entry.path,
                "title": video_entry.title or os.path.basename(video_entry.path),
                "duration": video_entry.duration,
                "is_youtube": video_entry.is_youtube,
                "youtube_id": video_entry.youtube_id,
                "youtube_url": video_entry.youtube_url,
                "quality": video_entry.quality,
                "custom_start_time": video_entry.custom_start_time,
                "custom_end_time": video_entry.custom_end_time,
                "playback_time": playback_time,
                "started_at": (
                    self.playback_engine.video_start_time.isoformat()
                    if self.playback_engine.video_start_time
                    else None
                ),
            }

    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        return self.playback_engine.is_playing()

    def is_in_cooldown(self) -> bool:
        """Check if we're in post-playback cooldown period."""
        if self.last_playback_end is None:
            return False

        cooldown_seconds = self.config.post_playback_cooldown_minutes * 60
        time_since_end = (datetime.now() - self.last_playback_end).total_seconds()
        return time_since_end < cooldown_seconds

    def can_start_video(self) -> bool:
        """Check if a new video can be started (not playing and not in cooldown)."""
        return not self.is_playing() and not self.is_in_cooldown()

    def stop_video(self, reason="manual"):
        """Stop currently playing video.
        
        Returns:
            True if a video was stopped, False if nothing was playing
        """
        turn_off_monitor = reason not in ("switch",)

        with self.process_lock:
            viewing_duration = self.playback_engine.stop_playback(reason)

            if viewing_duration is None:
                return False

            self.logger.info("Stopped video playback (reason: %s)", reason)

            if reason not in ("manual", "switch", "web"):
                self.last_playback_end = datetime.now()
            else:
                self.last_playback_end = None
                self.logger.debug("Clearing cooldown for manual/switch stop")

            if self.statistics_manager and self.current_video:
                self.statistics_manager.record_video_viewing(
                    self.current_video, viewing_duration, reason
                )

            self.current_video = None

        if turn_off_monitor:
            self.turn_monitor_off()

        return True

    def pause_video(self) -> bool:
        """Pause currently playing video.
        
        Returns:
            True if video was paused successfully, False otherwise
        """
        if not self.vlc_enabled:
            self.logger.warning("Pause not supported: VLC engine not available")
            return False
        
        if not self.is_playing():
            self.logger.warning("Cannot pause: no video is playing")
            return False
        
        return self.playback_engine.pause_playback()

    def resume_video(self) -> bool:
        """Resume paused video.
        
        Returns:
            True if video was resumed successfully, False otherwise
        """
        if not self.vlc_enabled:
            self.logger.warning("Resume not supported: VLC engine not available")
            return False
        
        # Check if there's a player (even if paused)
        if not hasattr(self.playback_engine, 'player') or self.playback_engine.player is None:
            self.logger.warning("Cannot resume: no video loaded")
            return False
        
        return self.playback_engine.resume_playback()

    def set_volume(self, volume: int) -> bool:
        """Set playback volume (0-100).
        
        Args:
            volume: Volume level from 0 (mute) to 100 (max)
            
        Returns:
            True if volume was set successfully, False otherwise
        """
        if not self.vlc_enabled:
            self.logger.warning("Volume control not supported: VLC engine not available")
            return False
        
        if not self.is_playing():
            self.logger.warning("Cannot set volume: no video is playing")
            return False
        
        # Clamp volume to 0-100
        volume = max(0, min(100, volume))
        return self.playback_engine.set_volume(volume)

    def is_paused(self) -> bool:
        """Check if video is currently paused.
        
        Returns:
            True if video is paused, False otherwise
        """
        if not self.vlc_enabled:
            return False
        
        return self.playback_engine.is_paused_state()

    def play_video(self, video_path: str, triggered_by: str = "api") -> bool:
        """Play a specific video by path.

        Args:
            video_path: Path to the video file or youtube:// URL
            triggered_by: How the video was triggered ('button', 'scheduled', 'api', 'web')

        Returns:
            True if playback started successfully, False otherwise
        """
        with self.process_lock:
            # Check if night mode playback is disabled
            if self.is_night_mode() and self.config.night_mode_disable_playback:
                self.logger.info("Cannot start video - playback disabled during night mode")
                return False

            # If a video is already playing, stop it first to allow switching videos
            if self.is_playing():
                self.logger.info("Stopping current video to switch to new one")
                self.stop_video(reason="switch")
            
            # Check if we're in cooldown (but not from the video we just stopped)
            if self.is_in_cooldown():
                remaining = (
                    self.config.post_playback_cooldown_minutes * 60
                    - (datetime.now() - self.last_playback_end).total_seconds()
                )
                self.logger.info("Cannot start video - in cooldown for %.0f more seconds", remaining)
                return False

            # Get video entry from library
            video_entry = self.get_video_entry(video_path)
            if not video_entry:
                self.logger.error("Video not found in library: %s", video_path)
                return False

            # Get the actual playback path (handles YouTube URLs, local files, etc.)
            playback_path = self._get_playback_path(video_entry)
            if not playback_path:
                self.logger.error("Could not get playback path for: %s", video_entry.get_display_title())
                return False

            self.logger.info(
                "Playing video: %s (triggered by: %s)",
                video_entry.get_display_title(),
                triggered_by,
            )

            # Get effective duration considering custom start/end times
            effective_duration = video_entry.get_playback_duration()
            if effective_duration is None or effective_duration <= 0:
                self.logger.error("Invalid effective duration for %s", video_entry.get_display_title())
                return False

            # Calculate playback parameters using custom start/end times
            custom_start = video_entry.custom_start_time
            custom_end = video_entry.custom_end_time or video_entry.duration

            # Determine how much of the video we'll actually play
            timeout_sec = self.config.playback_duration_minutes * 60
            available_duration = custom_end - custom_start

            if available_duration <= timeout_sec:
                # Play from custom start time for the available duration
                start_sec = custom_start
                actual_play_duration = available_duration
            else:
                # Pick a random start point within the custom range
                max_additional_start = available_duration - timeout_sec
                random_offset = random.uniform(0, max_additional_start)
                start_sec = custom_start + random_offset
                actual_play_duration = timeout_sec

            self.logger.info(
                "Playing %s from %.1fs for %.1fs (custom range: %.1f-%.1f)",
                video_entry.get_display_title(),
                start_sec,
                actual_play_duration,
                custom_start,
                custom_end,
            )

            # Prepare volume setting
            if self.is_night_mode():
                # Use night mode volume instead of muting
                night_volume = getattr(self.config, "night_mode_volume", 30)
                volume = night_volume
                self.logger.info("Night mode: using volume %d", night_volume)
            else:
                volume = self.config.volume

            # Turn on monitor
            self.turn_monitor_on()

            # Define callback for when video times out
            library_path = video_entry.path

            def on_timeout_callback(_engine_path, viewing_duration):
                """Handle video timeout."""
                self._handle_playback_finished(library_path, viewing_duration, "timeout")

            def on_complete_callback(_engine_path, viewing_duration):
                """Handle natural end of playback."""
                self._handle_playback_finished(library_path, viewing_duration, "completed")

            # Start video playback using the engine
            self.current_video = video_entry.path  # Track current video (for statistics)
            
            success = self.playback_engine.start_playback(
                video_path=playback_path,
                start_time=start_sec,
                volume=volume,
                duration=actual_play_duration,
                on_complete=on_complete_callback,
                on_timeout=on_timeout_callback,
            )

            if not success:
                self.logger.error("Failed to start video playback")
                self.current_video = None
                self.turn_monitor_off()
                return False

            # Record statistics
            if self.statistics_manager:
                self.statistics_manager.record_video_play(video_entry.path, triggered_by)

            self.logger.info("Video playback started successfully")
            return True

    def play_random_video(self, trigger: str = "button") -> bool:
        """Play a random video with timeout.

        Args:
            trigger: How the video was triggered ('button', 'scheduled', 'api')

        Returns:
            True if playback started successfully, False otherwise
        """
        # Check if night mode playback is disabled
        if self.is_night_mode() and self.config.night_mode_disable_playback:
            self.logger.info("Cannot start video - playback disabled during night mode")
            return False

        # Check if we can start a video (not playing and not in cooldown)
        if not self.can_start_video():
            if self.is_playing():
                self.logger.info("Cannot start video - already playing")
            elif self.is_in_cooldown():
                remaining = (
                    self.config.post_playback_cooldown_minutes * 60
                    - (datetime.now() - self.last_playback_end).total_seconds()
                )
                self.logger.info("Cannot start video - in cooldown for %.0f more seconds", remaining)
            return False

        # Get playable videos from library
        playable_videos = self.get_playable_videos()
        if not playable_videos:
            self.logger.warning("No playable videos found")
            return False

        # Select random video entry
        video_entry = random.choice(playable_videos)

        # Get the actual playback path (handles YouTube URLs, local files, etc.)
        playback_path = self._get_playback_path(video_entry)
        if not playback_path:
            self.logger.error("Could not get playback path for: %s", video_entry.get_display_title())
            return False

        self.logger.info(
            "Selected video: %s (title: %s)",
            video_entry.get_display_title(),
            video_entry.get_display_title(),
        )

        # Get effective duration considering custom start/end times
        effective_duration = video_entry.get_playback_duration()
        if effective_duration is None or effective_duration <= 0:
            self.logger.error("Invalid effective duration for %s", video_entry.get_display_title())
            return False

        # Calculate playback parameters using custom start/end times
        custom_start = video_entry.custom_start_time
        custom_end = video_entry.custom_end_time or video_entry.duration

        # Determine how much of the video we'll actually play
        timeout_sec = self.config.playback_duration_minutes * 60
        available_duration = custom_end - custom_start

        if available_duration <= timeout_sec:
            # Play from custom start time for the available duration
            start_sec = custom_start
            actual_play_duration = available_duration
        else:
            # Pick a random start point within the custom range
            max_additional_start = available_duration - timeout_sec
            random_offset = random.uniform(0, max_additional_start)
            start_sec = custom_start + random_offset
            actual_play_duration = timeout_sec

        self.logger.info(
            "Playing %s from %.1fs for %.1fs (custom range: %.1f-%.1f)",
            video_entry.get_display_title(),
            start_sec,
            actual_play_duration,
            custom_start,
            custom_end,
        )

        # Prepare volume setting
        if self.is_night_mode():
            # Use night mode volume instead of muting
            night_volume = getattr(self.config, "night_mode_volume", 30)
            volume = night_volume
            self.logger.info("Night mode: using volume %d", night_volume)
        else:
            volume = self.config.volume

        library_path = video_entry.path
        started = False

        def on_timeout_callback(_engine_path, viewing_duration):
            """Handle video timeout."""
            self._handle_playback_finished(library_path, viewing_duration, "timeout")

        def on_complete_callback(_engine_path, viewing_duration):
            """Handle natural end of playback."""
            self._handle_playback_finished(library_path, viewing_duration, "completed")

        with self.process_lock:
            if self.is_playing():
                self.logger.info("Cannot start random video - already playing")
                return False

            if self.is_in_cooldown():
                remaining = (
                    self.config.post_playback_cooldown_minutes * 60
                    - (datetime.now() - self.last_playback_end).total_seconds()
                ) if self.last_playback_end else 0
                self.logger.info("Cannot start video - in cooldown for %.0f more seconds", remaining)
                return False

            # Turn on monitor now that we're ready to start playback
            self.turn_monitor_on()

            # Start video playback using the engine
            self.current_video = library_path  # Track current video (for statistics)

            success = self.playback_engine.start_playback(
                video_path=playback_path,
                start_time=start_sec,
                volume=volume,
                duration=actual_play_duration,
                on_complete=on_complete_callback,
                on_timeout=on_timeout_callback,
            )

            if not success:
                self.logger.error("Failed to start video playback")
                self.current_video = None

            started = success

        if not started:
            self.turn_monitor_off()
            return False

        # Record statistics
        if self.statistics_manager:
            self.statistics_manager.record_video_play(library_path, trigger)

        self.logger.info("Video playback started successfully")
        return True

    def get_video_info(self) -> List[Dict]:
        """Get information about all videos with library metadata."""
        video_entries = self.get_video_library_entries()
        video_info = []

        for entry in video_entries:
            try:
                # Handle both local files and YouTube videos
                if entry.is_youtube:
                    # YouTube video
                    info = {
                        "path": entry.path,
                        "filename": entry.youtube_id or "YouTube Video",
                        "title": entry.title,
                        "display_title": entry.get_display_title(),
                        "size": entry.size or 0,
                        "size_mb": (round((entry.size or 0) / (1024 * 1024), 1) if entry.size else 0),
                        "modified": entry.added_time.isoformat() if entry.added_time else "",
                        "duration": entry.duration,
                        "duration_str": (format_duration(entry.duration) if entry.duration else "Unknown"),
                        "custom_start_time": entry.custom_start_time,
                        "custom_end_time": entry.custom_end_time,
                        "effective_duration": entry.get_playback_duration(),
                        "effective_duration_str": (
                            format_duration(entry.get_playback_duration())
                            if entry.get_playback_duration()
                            else "Unknown"
                        ),
                        # YouTube-specific fields
                        "is_youtube": True,
                        "youtube_id": entry.youtube_id,
                        "youtube_url": entry.youtube_url,
                        "quality": entry.quality,
                        "download_path": entry.download_path,
                        "stream_valid": entry.is_stream_valid(),
                    }
                    video_info.append(info)

                elif os.path.exists(entry.path):
                    # Local file
                    stat = os.stat(entry.path)

                    info = {
                        "path": entry.path,
                        "filename": os.path.basename(entry.path),
                        "title": entry.title,
                        "display_title": entry.get_display_title(),
                        "size": entry.size or stat.st_size,
                        "size_mb": round((entry.size or stat.st_size) / (1024 * 1024), 1),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "duration": entry.duration,
                        "duration_str": (format_duration(entry.duration) if entry.duration else "Unknown"),
                        "custom_start_time": entry.custom_start_time,
                        "custom_end_time": entry.custom_end_time,
                        "effective_duration": entry.get_playback_duration(),
                        "effective_duration_str": (
                            format_duration(entry.get_playback_duration())
                            if entry.get_playback_duration()
                            else "Unknown"
                        ),
                        # YouTube-specific fields (False for local files)
                        "is_youtube": False,
                        "youtube_id": None,
                        "youtube_url": None,
                        "quality": None,
                        "download_path": None,
                        "stream_valid": False,
                    }
                    video_info.append(info)

            except OSError as e:
                self.logger.error("Error getting info for %s: %s", entry.path, e)

        return sorted(video_info, key=lambda x: x["filename"].lower())

    def update_video_metadata(
        self,
        path: str,
        title: str = None,
        custom_start_time: float = None,
        custom_end_time: float = None,
    ) -> bool:
        """Update video metadata (title and custom times)."""
        return self.library_manager.update_video_metadata(path, title, custom_start_time, custom_end_time)

    def get_video_entry(self, path: str) -> Optional[VideoEntry]:
        """Get a video entry from the library."""
        return self.library_manager.get_video(path)

    def cleanup_cache(self):
        """Clean up old cache entries (now handled by database)."""
        # Cache cleanup is no longer needed - handled by database
