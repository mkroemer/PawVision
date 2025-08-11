"""Video library management with custom start/end times and titles."""

import logging
import os
from datetime import datetime
from typing import List, Optional, Tuple
from .database import PawVisionDatabase, VideoEntry
from .youtube_manager import YouTubeManager


class VideoLibraryManager:
    """Manages video library with custom metadata using unified database."""
    
    def __init__(self, db_path: str = "pawvision.db", video_directories: List[str] = None,
                 youtube_cache_dir: str = "youtube_cache", youtube_preferred_quality: str = "720p"):
        self.db = PawVisionDatabase(db_path)
        self.video_directories = video_directories or ["./videos"]
        self.youtube_manager = YouTubeManager(
            video_directories=self.video_directories,
            cache_dir=youtube_cache_dir,
            preferred_quality=youtube_preferred_quality
        )
        self.logger = logging.getLogger(__name__)
    
    def add_or_update_video(self, video_entry: VideoEntry) -> bool:
        """Add a new video or update existing entry."""
        return self.db.add_or_update_video(video_entry)
    
    def get_video(self, path: str) -> Optional[VideoEntry]:
        """Get a video entry by path."""
        return self.db.get_video(path)
    
    def get_all_videos(self) -> List[VideoEntry]:
        """Get all video entries."""
        return self.db.get_all_videos()
    
    def remove_video(self, path: str) -> bool:
        """Remove a video entry from the library."""
        return self.db.remove_video(path)
    
    def sync_with_filesystem(self, video_paths: List[str], duration_getter_func) -> Tuple[int, int, int]:
        """Sync library with actual filesystem.
        
        Args:
            video_paths: List of actual video file paths found on filesystem
            duration_getter_func: Function to get video duration
            
        Returns:
            Tuple of (added_count, updated_count, removed_count)
        """
        added_count = 0
        updated_count = 0
        removed_count = 0
        
        try:
            # Get current library entries
            current_entries = {entry.path: entry for entry in self.get_all_videos()}
            
            # Process existing files
            for video_path in video_paths:
                if not os.path.exists(video_path):
                    continue
                
                try:
                    stat = os.stat(video_path)
                    file_mtime = stat.st_mtime
                    file_size = stat.st_size
                    
                    existing_entry = current_entries.get(video_path)
                    
                    if existing_entry is None:
                        # New file - add to library
                        duration = duration_getter_func(video_path)
                        entry = VideoEntry(
                            path=video_path,
                            custom_start_time=0.0,
                            custom_end_time=None,
                            duration=duration,
                            size=file_size,
                            modified_time=file_mtime
                        )
                        
                        if self.add_or_update_video(entry):
                            added_count += 1
                            
                    elif (existing_entry.modified_time != file_mtime or 
                          existing_entry.size != file_size or
                          existing_entry.duration is None):
                        # File has been modified or missing metadata - update
                        duration = duration_getter_func(video_path)
                        existing_entry.duration = duration
                        existing_entry.size = file_size
                        existing_entry.modified_time = file_mtime
                        
                        if self.add_or_update_video(existing_entry):
                            updated_count += 1
                
                except OSError as e:
                    self.logger.error("Error processing file %s: %s", video_path, e)
            
            # Remove entries for files that no longer exist (but preserve YouTube videos)
            video_paths_set = set(video_paths)
            for entry_path, entry in current_entries.items():
                # Skip YouTube videos - they don't exist on filesystem
                if entry.is_youtube:
                    continue
                    
                # Remove local files that no longer exist
                if entry_path not in video_paths_set:
                    if self.remove_video(entry_path):
                        removed_count += 1
            
            if added_count > 0 or updated_count > 0 or removed_count > 0:
                self.logger.info("Library sync completed: %d added, %d updated, %d removed", 
                               added_count, updated_count, removed_count)
            
        except (ValueError, TypeError) as e:
            self.logger.error("Error during library sync: %s", e)
        
        return added_count, updated_count, removed_count
    
    def update_video_metadata(self, path: str, title: str = None, 
                             custom_start_time: float = None, 
                             custom_end_time: float = None) -> bool:
        """Update video metadata (title and custom times)."""
        return self.db.update_video_metadata(path, title, custom_start_time, custom_end_time)
    
    def get_playable_videos(self) -> List[VideoEntry]:
        """Get videos that have a valid playable duration."""
        videos = self.get_all_videos()
        playable = []
        
        for video in videos:
            if not os.path.exists(video.path):
                continue  # Skip missing files
            
            effective_duration = video.get_effective_duration()
            if effective_duration and effective_duration > 0:
                playable.append(video)
        
        return playable
    
    def export_to_json(self, export_path: str) -> bool:
        """Export library to JSON file for backup."""
        return self.db.export_to_json(export_path)
    
    # YouTube-specific methods
    
    def add_youtube_video(self, url: str, custom_title: str = None,
                         custom_start_time: float = 0.0,
                         custom_end_offset: float = None,  # Changed from custom_end_time to custom_end_offset
                         quality: str = "720p",
                         download: bool = False) -> bool:
        """Add a YouTube video to the library."""
        try:
            video_entry = self.youtube_manager.create_video_entry(
                url=url,
                custom_title=custom_title,
                custom_start_time=custom_start_time,
                custom_end_offset=custom_end_offset,  # Updated parameter name
                quality=quality,
                download=download
            )
            
            if video_entry:
                return self.add_or_update_video(video_entry)
            else:
                self.logger.error("Failed to create YouTube video entry for: %s", url)
                return False
                
        except (ValueError, TypeError, OSError) as e:
            self.logger.error("Error adding YouTube video %s: %s", url, e)
            return False
    
    def refresh_youtube_stream_urls(self) -> int:
        """Refresh expired YouTube stream URLs."""
        refreshed_count = 0
        youtube_videos = [v for v in self.get_all_videos() if v.is_youtube]
        
        for video in youtube_videos:
            if not video.is_stream_valid():
                if self.youtube_manager.refresh_stream_url(video):
                    if self.add_or_update_video(video):
                        refreshed_count += 1
                        self.logger.debug("Refreshed stream URL for: %s", video.get_display_title())
        
        if refreshed_count > 0:
            self.logger.info("Refreshed %d YouTube stream URLs", refreshed_count)
        
        return refreshed_count
    
    def download_youtube_video(self, video_path: str, quality: str = None) -> bool:
        """Download a YouTube video for offline playback."""
        video = self.get_video(video_path)
        if not video or not video.is_youtube:
            return False
        
        download_path = self.youtube_manager.download_video(video.youtube_id, quality)
        if download_path:
            video.download_path = download_path
            video.updated_at = datetime.now().isoformat()
            return self.add_or_update_video(video)
        
        return False
    
    def get_youtube_videos(self) -> List[VideoEntry]:
        """Get all YouTube videos in the library."""
        return [v for v in self.get_all_videos() if v.is_youtube]
    
    def get_local_videos(self) -> List[VideoEntry]:
        """Get all local (non-YouTube) videos in the library."""
        return [v for v in self.get_all_videos() if not v.is_youtube]
    
    def cleanup_youtube_downloads(self, max_age_days: int = 30):
        """Clean up old YouTube downloads."""
        self.youtube_manager.cleanup_expired_downloads(max_age_days)
