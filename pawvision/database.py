"""Unified database manager for PawVision video library and statistics."""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class VideoEntry:
    """Represents a video entry in the library."""
    path: str
    title: Optional[str] = None
    custom_start_time: float = 0.0  # seconds from beginning
    custom_end_time: Optional[float] = None  # seconds from beginning, None = full duration
    duration: Optional[float] = None  # total video duration in seconds
    size: Optional[int] = None  # file size in bytes
    modified_time: Optional[float] = None  # file modification timestamp
    created_at: Optional[str] = None  # when entry was created
    updated_at: Optional[str] = None  # when entry was last updated
    # YouTube-specific fields
    is_youtube: bool = False  # whether this is a YouTube video
    youtube_id: Optional[str] = None  # YouTube video ID
    youtube_url: Optional[str] = None  # original YouTube URL
    stream_url: Optional[str] = None  # direct stream URL (expires)
    stream_expires: Optional[str] = None  # when stream URL expires
    download_path: Optional[str] = None  # path to downloaded file if cached
    quality: Optional[str] = None  # video quality preference
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        now = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    def get_effective_duration(self) -> Optional[float]:
        """Get the effective playback duration considering custom start/end times."""
        if self.duration is None:
            return None
        
        start = max(0, self.custom_start_time)
        end = min(self.duration, self.custom_end_time or self.duration)
        
        if end <= start:
            return 0
        
        return end - start
    
    def get_display_title(self) -> str:
        """Get the title to display (custom title or filename)."""
        if self.title:
            return self.title
        if self.is_youtube:
            # For YouTube videos, use the video ID as fallback
            return f"YouTube Video {self.youtube_id}" if self.youtube_id else "YouTube Video"
        return os.path.basename(self.path)
    
    def is_stream_valid(self) -> bool:
        """Check if the stream URL is still valid (not expired)."""
        if not self.stream_url or not self.stream_expires:
            return False
        try:
            expires = datetime.fromisoformat(self.stream_expires)
            return datetime.now() < expires
        except (ValueError, TypeError):
            return False
    
    def get_playback_path(self) -> str:
        """Get the path/URL to use for playback."""
        if self.is_youtube:
            # Prefer downloaded file if available
            if self.download_path and os.path.exists(self.download_path):
                return self.download_path
            # Use stream URL if valid
            elif self.is_stream_valid():
                return self.stream_url
            # Fall back to YouTube URL (will need fresh stream URL)
            else:
                return self.youtube_url or self.path
        return self.path


class PawVisionDatabase:
    """Unified database manager for video library and statistics."""
    
    def __init__(self, db_path: str = "pawvision.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with all required tables."""
        try:
            # Ensure directory exists (only if not current directory)
            db_dir = os.path.dirname(self.db_path)
            if db_dir:  # Only create directory if path contains a directory
                os.makedirs(db_dir, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Video library table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS video_library (
                        path TEXT PRIMARY KEY,
                        title TEXT,
                        custom_start_time REAL NOT NULL DEFAULT 0.0,
                        custom_end_time REAL,
                        duration REAL,
                        size INTEGER,
                        modified_time REAL,
                        created_at TEXT,
                        updated_at TEXT,
                        is_youtube BOOLEAN NOT NULL DEFAULT 0,
                        youtube_id TEXT,
                        youtube_url TEXT,
                        stream_url TEXT,
                        stream_expires TEXT,
                        download_path TEXT,
                        quality TEXT
                    )
                """)
                
                # Statistics events table (detailed event logging)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT NOT NULL,
                        action TEXT,
                        details TEXT,
                        video_file TEXT,
                        duration REAL,
                        source TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Statistics summary table (aggregated statistics)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS statistics_summary (
                        id INTEGER PRIMARY KEY,
                        category TEXT NOT NULL,
                        subcategory TEXT,
                        key TEXT NOT NULL,
                        value_type TEXT NOT NULL,  -- 'int', 'float', 'string', 'json'
                        int_value INTEGER,
                        float_value REAL,
                        string_value TEXT,
                        json_value TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(category, subcategory, key)
                    )
                """)
                
                # Indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_video_modified_time ON video_library(modified_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_video_updated_at ON video_library(updated_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_action ON events(action)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_category ON statistics_summary(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stats_key ON statistics_summary(key)")
                
                conn.commit()
                self.logger.info("PawVision database initialized at %s", self.db_path)
                
        except sqlite3.Error as e:
            self.logger.error("Error initializing database: %s", e)
            raise
    
    # =============================================================================
    # VIDEO LIBRARY METHODS
    # =============================================================================
    
    def add_or_update_video(self, video_entry: VideoEntry) -> bool:
        """Add a new video or update existing entry."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Check if video already exists
                    cursor = conn.execute("SELECT path FROM video_library WHERE path = ?", (video_entry.path,))
                    exists = cursor.fetchone() is not None
                    
                    if exists:
                        # Update existing entry
                        video_entry.updated_at = datetime.now().isoformat()
                        conn.execute("""
                            UPDATE video_library SET
                                title = ?,
                                custom_start_time = ?,
                                custom_end_time = ?,
                                duration = ?,
                                size = ?,
                                modified_time = ?,
                                updated_at = ?,
                                is_youtube = ?,
                                youtube_id = ?,
                                youtube_url = ?,
                                stream_url = ?,
                                stream_expires = ?,
                                download_path = ?,
                                quality = ?
                            WHERE path = ?
                        """, (
                            video_entry.title,
                            video_entry.custom_start_time,
                            video_entry.custom_end_time,
                            video_entry.duration,
                            video_entry.size,
                            video_entry.modified_time,
                            video_entry.updated_at,
                            video_entry.is_youtube,
                            video_entry.youtube_id,
                            video_entry.youtube_url,
                            video_entry.stream_url,
                            video_entry.stream_expires,
                            video_entry.download_path,
                            video_entry.quality,
                            video_entry.path
                        ))
                        self.logger.debug("Updated video entry: %s", video_entry.path)
                    else:
                        # Insert new entry
                        conn.execute("""
                            INSERT INTO video_library (
                                path, title, custom_start_time, custom_end_time,
                                duration, size, modified_time, created_at, updated_at,
                                is_youtube, youtube_id, youtube_url, stream_url,
                                stream_expires, download_path, quality
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            video_entry.path,
                            video_entry.title,
                            video_entry.custom_start_time,
                            video_entry.custom_end_time,
                            video_entry.duration,
                            video_entry.size,
                            video_entry.modified_time,
                            video_entry.created_at,
                            video_entry.updated_at,
                            video_entry.is_youtube,
                            video_entry.youtube_id,
                            video_entry.youtube_url,
                            video_entry.stream_url,
                            video_entry.stream_expires,
                            video_entry.download_path,
                            video_entry.quality
                        ))
                        self.logger.debug("Added new video entry: %s", video_entry.path)
                    
                    conn.commit()
                    return True
                    
        except sqlite3.Error as e:
            self.logger.error("Error adding/updating video %s: %s", video_entry.path, e)
            return False
    
    def get_video(self, path: str) -> Optional[VideoEntry]:
        """Get a video entry by path."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT * FROM video_library WHERE path = ?
                    """, (path,))
                    
                    row = cursor.fetchone()
                    if row:
                        # Convert sqlite3.Row to dict for easier access
                        row_dict = dict(row)
                        return VideoEntry(
                            path=row_dict['path'],
                            title=row_dict['title'],
                            custom_start_time=row_dict['custom_start_time'],
                            custom_end_time=row_dict['custom_end_time'],
                            duration=row_dict['duration'],
                            size=row_dict['size'],
                            modified_time=row_dict['modified_time'],
                            created_at=row_dict['created_at'],
                            updated_at=row_dict['updated_at'],
                            is_youtube=bool(row_dict.get('is_youtube', False)),
                            youtube_id=row_dict.get('youtube_id'),
                            youtube_url=row_dict.get('youtube_url'),
                            stream_url=row_dict.get('stream_url'),
                            stream_expires=row_dict.get('stream_expires'),
                            download_path=row_dict.get('download_path'),
                            quality=row_dict.get('quality')
                        )
                    return None
                    
        except sqlite3.Error as e:
            self.logger.error("Error getting video %s: %s", path, e)
            return None
    
    def get_all_videos(self) -> List[VideoEntry]:
        """Get all video entries."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT * FROM video_library ORDER BY updated_at DESC
                    """)
                    
                    videos = []
                    for row in cursor.fetchall():
                        # Convert sqlite3.Row to dict for easier access
                        row_dict = dict(row)
                        videos.append(VideoEntry(
                            path=row_dict['path'],
                            title=row_dict['title'],
                            custom_start_time=row_dict['custom_start_time'],
                            custom_end_time=row_dict['custom_end_time'],
                            duration=row_dict['duration'],
                            size=row_dict['size'],
                            modified_time=row_dict['modified_time'],
                            created_at=row_dict['created_at'],
                            updated_at=row_dict['updated_at'],
                            is_youtube=bool(row_dict.get('is_youtube', False)),
                            youtube_id=row_dict.get('youtube_id'),
                            youtube_url=row_dict.get('youtube_url'),
                            stream_url=row_dict.get('stream_url'),
                            stream_expires=row_dict.get('stream_expires'),
                            download_path=row_dict.get('download_path'),
                            quality=row_dict.get('quality')
                        ))
                    
                    return videos
                    
        except sqlite3.Error as e:
            self.logger.error("Error getting all videos: %s", e)
            return []
    
    def remove_video(self, path: str) -> bool:
        """Remove a video entry from the library."""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("DELETE FROM video_library WHERE path = ?", (path,))
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        self.logger.debug("Removed video entry: %s", path)
                        return True
                    else:
                        self.logger.warning("Video entry not found for removal: %s", path)
                        return False
                    
        except sqlite3.Error as e:
            self.logger.error("Error removing video %s: %s", path, e)
            return False
    
    def update_video_metadata(self, path: str, title: str = None, 
                             custom_start_time: float = None, 
                             custom_end_time: float = None) -> bool:
        """Update video metadata (title and custom times)."""
        try:
            entry = self.get_video(path)
            if entry is None:
                # Create new entry if it doesn't exist
                entry = VideoEntry(path=path)
            
            # Update provided fields
            if title is not None:
                entry.title = title.strip() if title.strip() else None
            
            if custom_start_time is not None:
                entry.custom_start_time = max(0, custom_start_time)
            
            if custom_end_time is not None:
                if entry.duration and custom_end_time > entry.duration:
                    entry.custom_end_time = entry.duration
                elif custom_end_time <= entry.custom_start_time:
                    entry.custom_end_time = None  # Invalid range, use full duration
                else:
                    entry.custom_end_time = custom_end_time
            
            entry.updated_at = datetime.now().isoformat()
            
            return self.add_or_update_video(entry)
            
        except (ValueError, TypeError) as e:
            self.logger.error("Error updating video metadata for %s: %s", path, e)
            return False
    
    # =============================================================================
    # STATISTICS METHODS
    # =============================================================================
    
    def log_event(self, event_type: str, action: str = None, details: Dict = None, 
                  video_file: str = None, duration: float = None, source: str = 'system'):
        """Log an event to the events table."""
        try:
            details_json = json.dumps(details) if details else None
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO events (event_type, action, details, video_file, duration, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (event_type, action, details_json, video_file, duration, source))
                conn.commit()
                
            self.logger.debug("Event logged: %s - %s", event_type, action)
            
        except sqlite3.Error as e:
            self.logger.error("Failed to log event: %s", e)
    
    def set_statistic(self, category: str, key: str, value, subcategory: str = None):
        """Set a statistic value in the summary table."""
        try:
            # Determine value type and column
            if isinstance(value, bool):
                value_type, col_value = 'int', int(value)
            elif isinstance(value, int):
                value_type, col_value = 'int', value
            elif isinstance(value, float):
                value_type, col_value = 'float', value
            elif isinstance(value, str):
                value_type, col_value = 'string', value
            else:
                value_type, col_value = 'json', json.dumps(value)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO statistics_summary 
                    (category, subcategory, key, value_type, int_value, float_value, string_value, json_value, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    category, subcategory, key, value_type,
                    col_value if value_type == 'int' else None,
                    col_value if value_type == 'float' else None,
                    col_value if value_type == 'string' else None,
                    col_value if value_type == 'json' else None,
                    datetime.now().isoformat()
                ))
                conn.commit()
                
        except sqlite3.Error as e:
            self.logger.error("Failed to set statistic %s.%s: %s", category, key, e)
    
    def get_statistic(self, category: str, key: str, subcategory: str = None, default=None):
        """Get a statistic value from the summary table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT value_type, int_value, float_value, string_value, json_value
                    FROM statistics_summary 
                    WHERE category = ? AND key = ? AND (subcategory = ? OR (subcategory IS NULL AND ? IS NULL))
                """, (category, key, subcategory, subcategory))
                
                row = cursor.fetchone()
                if row:
                    if row['value_type'] == 'int':
                        return row['int_value']
                    elif row['value_type'] == 'float':
                        return row['float_value']
                    elif row['value_type'] == 'string':
                        return row['string_value']
                    elif row['value_type'] == 'json':
                        return json.loads(row['json_value'])
                
                return default
                
        except (sqlite3.Error, json.JSONDecodeError) as e:
            self.logger.error("Failed to get statistic %s.%s: %s", category, key, e)
            return default
    
    def get_statistics_by_category(self, category: str) -> Dict:
        """Get all statistics for a category."""
        try:
            stats = {}
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT subcategory, key, value_type, int_value, float_value, string_value, json_value
                    FROM statistics_summary 
                    WHERE category = ?
                """, (category,))
                
                for row in cursor.fetchall():
                    # Get the value based on type
                    if row['value_type'] == 'int':
                        value = row['int_value']
                    elif row['value_type'] == 'float':
                        value = row['float_value']
                    elif row['value_type'] == 'string':
                        value = row['string_value']
                    elif row['value_type'] == 'json':
                        value = json.loads(row['json_value'])
                    else:
                        continue
                    
                    # Build nested structure
                    if row['subcategory']:
                        if row['subcategory'] not in stats:
                            stats[row['subcategory']] = {}
                        stats[row['subcategory']][row['key']] = value
                    else:
                        stats[row['key']] = value
                
                return stats
                
        except (sqlite3.Error, json.JSONDecodeError) as e:
            self.logger.error("Failed to get statistics for category %s: %s", category, e)
            return {}
    
    def migrate_json_statistics(self, json_file_path: str) -> bool:
        """Migrate existing JSON statistics to the database."""
        if not os.path.exists(json_file_path):
            self.logger.info("No JSON statistics file to migrate: %s", json_file_path)
            return True
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            # Migrate each category
            for category, category_data in stats.items():
                if isinstance(category_data, dict):
                    for key, value in category_data.items():
                        if isinstance(value, dict):
                            # This is a subcategory
                            for subkey, subvalue in value.items():
                                self.set_statistic(category, subkey, subvalue, key)
                        else:
                            # This is a direct value
                            self.set_statistic(category, key, value)
                else:
                    # Direct category value
                    self.set_statistic('root', category, category_data)
            
            # Backup the original file
            backup_path = f"{json_file_path}.migrated.backup"
            os.rename(json_file_path, backup_path)
            self.logger.info("Statistics migrated from JSON to database. Original backed up to: %s", backup_path)
            return True
            
        except (OSError, json.JSONDecodeError, ValueError) as e:
            self.logger.error("Failed to migrate JSON statistics: %s", e)
            return False
    
    def export_to_json(self, export_path: str) -> bool:
        """Export both video library and statistics to JSON file."""
        try:
            # Get all videos
            videos = self.get_all_videos()
            
            # Get all statistics by category
            all_stats = {}
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT DISTINCT category FROM statistics_summary")
                categories = [row['category'] for row in cursor.fetchall()]
                
                for category in categories:
                    all_stats[category] = self.get_statistics_by_category(category)
            
            # Export data
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'database_path': self.db_path,
                'video_library': {
                    'total_videos': len(videos),
                    'videos': [asdict(video) for video in videos]
                },
                'statistics': all_stats
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Database exported to %s", export_path)
            return True
            
        except (OSError, ValueError) as e:
            self.logger.error("Error exporting database: %s", e)
            return False
