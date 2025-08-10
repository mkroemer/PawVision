"""Video library management with custom start/end times and titles."""

import logging
import os
from typing import List, Optional, Tuple
from .database import PawVisionDatabase, VideoEntry


class VideoLibraryManager:
    """Manages video library with custom metadata using unified database."""
    
    def __init__(self, db_path: str = "pawvision.db"):
        self.db = PawVisionDatabase(db_path)
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
            
            # Remove entries for files that no longer exist
            video_paths_set = set(video_paths)
            for entry_path in current_entries:
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
