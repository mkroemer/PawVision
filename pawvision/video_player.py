"""Video player with proper process management and caching."""

import json
import logging
import os
import random
import subprocess
import threading
import time
import signal
import atexit
from datetime import datetime
from threading import Lock
from typing import List, Optional, Dict
from .time_utils import time_parser
from .video_library import VideoLibraryManager
from .database import VideoEntry


class VideoCache:
    """Manages video duration caching."""
    
    def __init__(self, cache_file: str, enabled: bool = True):
        self.cache_file = cache_file
        self.enabled = enabled
        self.cache_lock = Lock()
        self.logger = logging.getLogger(__name__)
        self._cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, float]:
        """Load cache from file."""
        if not self.enabled:
            return {}
        
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                self.logger.info("Duration cache loaded from %s", self.cache_file)
                return cache_data
            else:
                self.logger.info("Cache file not found, starting with empty cache")
                return {}
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error("Error loading cache: %s", e)
            return {}
    
    def _save_cache(self):
        """Save cache to file."""
        if not self.enabled:
            return
        
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            with self.cache_lock:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, indent=2)
            
            self.logger.debug("Duration cache saved")
        except OSError as e:
            self.logger.error("Error saving cache: %s", e)
    
    def get_duration(self, file_path: str) -> Optional[float]:
        """Get cached duration for a file."""
        if not self.enabled:
            return None
        
        try:
            # Use file path + modification time as cache key
            mtime = os.path.getmtime(file_path)
            cache_key = f"{file_path}:{mtime}"
            
            with self.cache_lock:
                return self._cache.get(cache_key)
        except OSError:
            return None
    
    def set_duration(self, file_path: str, duration: float):
        """Cache duration for a file."""
        if not self.enabled:
            return
        
        try:
            mtime = os.path.getmtime(file_path)
            cache_key = f"{file_path}:{mtime}"
            
            with self.cache_lock:
                self._cache[cache_key] = duration
            
            self._save_cache()
        except OSError as e:
            self.logger.error("Error caching duration for %s: %s", file_path, e)
    
    def cleanup_old_entries(self):
        """Remove cache entries for files that no longer exist."""
        if not self.enabled:
            return
        
        removed_count = 0
        with self.cache_lock:
            keys_to_remove = []
            for cache_key in self._cache:
                file_path = cache_key.split(':')[0]
                if not os.path.exists(file_path):
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self._cache[key]
                removed_count += 1
        
        if removed_count > 0:
            self._save_cache()
            self.logger.info("Cleaned up %d old cache entries", removed_count)


class VideoPlayer:
    """Manages video playback with proper process management."""
    
    def __init__(self, config, video_dirs, statistics_manager=None, monitor_manager=None):
        """Initialize the video player with configuration and video directories."""
        self.config = config
        self.video_dirs = video_dirs
        self.statistics_manager = statistics_manager
        self.monitor_manager = monitor_manager
        self.process_lock = threading.Lock()
        self.current_process = None
        self.current_video = None
        self.last_playback_end = None  # Track when last video ended
        self.video_start_time = None  # Track when current video started
        self.motion_detected = False  # Track motion sensor state
        
        # Initialize video library manager
        db_path = getattr(config, 'database_path', 'pawvision.db')
        youtube_cache_dir = getattr(config, 'youtube_cache_dir', 'youtube_cache')
        youtube_preferred_quality = getattr(config, 'youtube_preferred_quality', '720p')
        self.library_manager = VideoLibraryManager(
            db_path=db_path,
            video_directories=video_dirs,
            youtube_cache_dir=youtube_cache_dir,
            youtube_preferred_quality=youtube_preferred_quality
        )
        self.monitor_relay = None
        self.timeout_thread = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache
        self.cache = VideoCache(
            config.cache_file,
            config.enable_duration_cache
        )
        
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
                if hasattr(self.config, 'dev_mode') and not getattr(self.config, 'dev_mode', False):
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
        with self.process_lock:
            if self.current_process and self.current_process.poll() is None:
                self.logger.info("Terminating video process")
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=5)
                except (subprocess.TimeoutExpired, OSError):
                    pass
    
    def sync_video_library(self):
        """Sync the video library with filesystem."""
        video_files = self.get_all_video_files()
        added, updated, removed = self.library_manager.sync_with_filesystem(
            video_files, self.get_video_duration
        )
        if added > 0 or updated > 0 or removed > 0:
            self.logger.info("Video library synced: %d added, %d updated, %d removed", 
                           added, updated, removed)
    
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
        
        # Handle YouTube videos
        playback_path = video_entry.get_playback_path()
        
        # If we got a YouTube URL back, we need to refresh the stream URL
        if playback_path and playback_path.startswith(('https://www.youtube.com', 'https://youtu.be')):
            self.logger.info("Refreshing stream URL for YouTube video: %s", 
                           video_entry.get_display_title())
            
            if self.library_manager.youtube_manager.refresh_stream_url(video_entry):
                # Update the database with new stream URL
                self.library_manager.add_or_update_video(video_entry)
                playback_path = video_entry.stream_url
            else:
                self.logger.error("Failed to refresh stream URL for: %s", 
                                video_entry.get_display_title())
                return None
        
        return playback_path
    
    def get_all_video_files(self) -> List[str]:
        """Get list of all video files in configured directories (filesystem scan)."""
        videos = []
        supported_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm')
        
        for vdir in self.video_dirs:
            if not os.path.exists(vdir):
                self.logger.warning("Video directory does not exist: %s", vdir)
                continue
            
            try:
                for filename in os.listdir(vdir):
                    if filename.lower().endswith(supported_extensions):
                        full_path = os.path.join(vdir, filename)
                        if os.path.isfile(full_path):
                            videos.append(full_path)
            except OSError as e:
                self.logger.error("Error reading video directory %s: %s", vdir, e)
        
        self.logger.debug("Found %d videos", len(videos))
        return videos

    def get_all_videos(self) -> List[str]:
        """Get list of all video files (for backward compatibility)."""
        return self.get_all_video_files()
    
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
    
    def get_video_duration(self, file_path: str) -> Optional[float]:
        """Get video duration in seconds using mediainfo with caching."""
        if not os.path.exists(file_path):
            self.logger.warning("Video file not found: %s", file_path)
            return None
        
        # Check cache first
        cached_duration = self.cache.get_duration(file_path)
        if cached_duration is not None:
            self.logger.debug("Using cached duration for %s", os.path.basename(file_path))
            return cached_duration
        
        # Get duration using mediainfo
        try:
            result = subprocess.run(
                ["mediainfo", "--Inform=Video;%Duration%", file_path],
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            
            if result.returncode != 0:
                self.logger.error("mediainfo failed for %s: %s", file_path, result.stderr)
                return None
            
            duration_str = result.stdout.strip()
            if not duration_str:
                self.logger.warning("No duration found for %s", file_path)
                return None
            
            # Duration is in milliseconds, convert to seconds
            duration_ms = int(duration_str)
            duration_sec = duration_ms / 1000.0
            
            # Cache the result
            self.cache.set_duration(file_path, duration_sec)
            
            self.logger.debug("Got duration for %s: %.1f seconds", 
                            os.path.basename(file_path), duration_sec)
            return duration_sec
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout getting duration for %s", file_path)
            return None
        except (ValueError, OSError) as e:
            self.logger.error("Error getting duration for %s: %s", file_path, e)
            return None
    
    def is_night_mode(self) -> bool:
        """Check if current time is in night mode."""
        return time_parser.is_time_in_range(
            self.config.night_mode_start,
            self.config.night_mode_end
        )
    
    def turn_monitor_on(self):
        """Turn monitor on."""
        dev_mode = getattr(self.config, 'dev_mode', False)
        
        if dev_mode:
            self.logger.info("DEV_MODE: Would turn monitor on")
            return
        
        try:
            if self.monitor_relay:
                self.monitor_relay.on()
                self.logger.info("Monitor turned on via GPIO")
            else:
                subprocess.run("vcgencmd display_power 1", shell=True, check=False)
                self.logger.info("Monitor turned on via vcgencmd")
        except (AttributeError, OSError) as e:
            self.logger.error("Error turning monitor on: %s", e)
    
    def turn_monitor_off(self):
        """Turn monitor off."""
        dev_mode = getattr(self.config, 'dev_mode', False)
        
        if dev_mode:
            self.logger.info("DEV_MODE: Would turn monitor off")
            return
        
        try:
            if self.monitor_relay:
                self.monitor_relay.off()
                self.logger.info("Monitor turned off via GPIO")
            else:
                subprocess.run("vcgencmd display_power 0", shell=True, check=False)
                self.logger.info("Monitor turned off via vcgencmd")
        except (AttributeError, OSError) as e:
            self.logger.error("Error turning monitor off: %s", e)
    
    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        with self.process_lock:
            return (self.current_process is not None and 
                   self.current_process.poll() is None)
    
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
        """Stop currently playing video."""
        with self.process_lock:
            if self.current_process and self.current_process.poll() is None:
                self.logger.info("Stopping video playback (reason: %s)", reason)
                
                # Calculate viewing duration before stopping
                viewing_duration = None
                if self.video_start_time:
                    viewing_duration = (datetime.now() - self.video_start_time).total_seconds()
                
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Video process did not terminate, killing")
                    self.current_process.kill()
                
                # Record the end time and viewing duration
                self.last_playback_end = datetime.now()
                
                # Record viewing statistics
                if self.statistics_manager and self.current_video and viewing_duration:
                    self.statistics_manager.record_video_viewing(
                        self.current_video, 
                        viewing_duration, 
                        reason
                    )
                
                self.current_video = None  # Clear current video
                self.video_start_time = None
                self.turn_monitor_off()
                
                # Cancel timeout thread
                if self.timeout_thread and self.timeout_thread.is_alive():
                    # We can't actually cancel the thread, but the check in stop_after_timeout
                    # will prevent it from doing anything
                    pass
                
                return True
        
        return False
        
    def play_random_video(self, trigger: str = "button") -> bool:
        """Play a random video with timeout.
        
        Args:
            trigger: How the video was triggered ('button', 'scheduled', 'api')
            
        Returns:
            True if playback started successfully, False otherwise
        """
        # Check if we can start a video (not playing and not in cooldown)
        if not self.can_start_video():
            if self.is_playing():
                self.logger.info("Cannot start video - already playing")
            elif self.is_in_cooldown():
                remaining = self.config.post_playback_cooldown_minutes * 60 - \
                           (datetime.now() - self.last_playback_end).total_seconds()
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
        
        self.logger.info("Selected video: %s (title: %s)", 
                        video_entry.get_display_title(), video_entry.get_display_title())
        
        # Get effective duration considering custom start/end times
        effective_duration = video_entry.get_effective_duration()
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
        
        self.logger.info("Playing %s from %.1fs for %.1fs (custom range: %.1f-%.1f)", 
                        video_entry.get_display_title(), start_sec, actual_play_duration,
                        custom_start, custom_end)
        
        # Prepare volume setting
        if self.is_night_mode():
            volume_arg = "--volume=0"
            self.logger.info("Night mode: video will be muted")
        else:
            volume_arg = f"--volume={self.config.volume}"
        
        # Turn on monitor
        self.turn_monitor_on()
        
        # Start video playback
        try:
            with self.process_lock:
                self.current_video = video_entry.path  # Track current video (for statistics)
                self.video_start_time = datetime.now()  # Track start time
                self.current_process = subprocess.Popen([
                    "mpv",
                    f"--start={start_sec}",
                    volume_arg,
                    "--really-quiet",  # Reduce mpv output
                    playback_path
                ])
            
            # Record statistics
            if self.statistics_manager:
                self.statistics_manager.record_video_play(video_entry.path, trigger)
            
            # Start timeout thread
            self.timeout_thread = threading.Thread(
                target=self._stop_after_timeout,
                args=(actual_play_duration,),
                daemon=True
            )
            self.timeout_thread.start()
            
            self.logger.info("Video playback started successfully")
            return True
            
        except OSError as e:
            self.logger.error("Error starting video playback: %s", e)
            self.turn_monitor_off()
            return False
    
    def _stop_after_timeout(self, timeout_sec: int):
        """Stop video after timeout period."""
        time.sleep(timeout_sec)
        
        with self.process_lock:
            if self.current_process and self.current_process.poll() is None:
                self.logger.info("Video timeout reached, stopping playback")
                
                # Calculate viewing duration 
                viewing_duration = None
                if self.video_start_time:
                    viewing_duration = (datetime.now() - self.video_start_time).total_seconds()
                
                self.current_process.terminate()
                
                # Record the end time and viewing duration
                self.last_playback_end = datetime.now()
                
                # Record viewing statistics
                if self.statistics_manager and self.current_video and viewing_duration:
                    self.statistics_manager.record_video_viewing(
                        self.current_video, 
                        viewing_duration, 
                        "timeout"
                    )
                
                self.current_video = None  # Clear current video
                self.video_start_time = None
                self.turn_monitor_off()
    
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
                        'path': entry.path,
                        'filename': entry.youtube_id or "YouTube Video",
                        'title': entry.title,
                        'display_title': entry.get_display_title(),
                        'size': entry.size or 0,
                        'size_mb': round((entry.size or 0) / (1024 * 1024), 1) if entry.size else 0,
                        'modified': entry.updated_at or entry.created_at or "",
                        'duration': entry.duration,
                        'duration_str': self._format_duration(entry.duration) if entry.duration else "Unknown",
                        'custom_start_time': entry.custom_start_time,
                        'custom_end_time': entry.custom_end_time,
                        'effective_duration': entry.get_effective_duration(),
                        'effective_duration_str': self._format_duration(entry.get_effective_duration()) if entry.get_effective_duration() else "Unknown",
                        # YouTube-specific fields
                        'is_youtube': True,
                        'youtube_id': entry.youtube_id,
                        'youtube_url': entry.youtube_url,
                        'quality': entry.quality,
                        'download_path': entry.download_path,
                        'stream_valid': entry.is_stream_valid()
                    }
                    video_info.append(info)
                    
                elif os.path.exists(entry.path):
                    # Local file
                    stat = os.stat(entry.path)
                    
                    info = {
                        'path': entry.path,
                        'filename': os.path.basename(entry.path),
                        'title': entry.title,
                        'display_title': entry.get_display_title(),
                        'size': entry.size or stat.st_size,
                        'size_mb': round((entry.size or stat.st_size) / (1024 * 1024), 1),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'duration': entry.duration,
                        'duration_str': self._format_duration(entry.duration) if entry.duration else "Unknown",
                        'custom_start_time': entry.custom_start_time,
                        'custom_end_time': entry.custom_end_time,
                        'effective_duration': entry.get_effective_duration(),
                        'effective_duration_str': self._format_duration(entry.get_effective_duration()) if entry.get_effective_duration() else "Unknown",
                        # YouTube-specific fields (False for local files)
                        'is_youtube': False,
                        'youtube_id': None,
                        'youtube_url': None,
                        'quality': None,
                        'download_path': None,
                        'stream_valid': False
                    }
                    video_info.append(info)
                
            except OSError as e:
                self.logger.error("Error getting info for %s: %s", entry.path, e)
        
        return sorted(video_info, key=lambda x: x['filename'].lower())
    
    def update_video_metadata(self, path: str, title: str = None, 
                             custom_start_time: float = None, 
                             custom_end_time: float = None) -> bool:
        """Update video metadata (title and custom times)."""
        return self.library_manager.update_video_metadata(
            path, title, custom_start_time, custom_end_time
        )
    
    def get_video_entry(self, path: str) -> Optional[VideoEntry]:
        """Get a video entry from the library."""
        return self.library_manager.get_video(path)
    
    def _format_duration(self, duration: float) -> str:
        """Format duration in seconds to readable string."""
        if duration < 60:
            return f"{int(duration)}s"
        elif duration < 3600:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def cleanup_cache(self):
        """Clean up old cache entries."""
        self.cache.cleanup_old_entries()
