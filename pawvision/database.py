"""Database models and access layer for PawVision."""

import json
import logging
import os
import sqlite3
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from threading import Lock


@dataclass
class VideoEntry:
    """Represents a video entry in the library with metadata."""

    # Core identification
    path: str  # File path for local videos, youtube:// scheme for YouTube videos

    # Display metadata
    title: Optional[str] = None  # Custom title, if None will use filename/YouTube title

    # Playback settings
    custom_start_time: float = 0.0  # Start playback at this timestamp (seconds)
    custom_end_time: Optional[float] = None  # End playback at this timestamp (seconds)
    duration: Optional[float] = None  # Total video duration (seconds)

    # File metadata (for local files)
    size: Optional[int] = None  # File size in bytes
    modified_time: Optional[float] = None  # File modification timestamp

    # YouTube-specific fields
    is_youtube: bool = False
    youtube_id: Optional[str] = None
    youtube_url: Optional[str] = None
    stream_url: Optional[str] = None  # Direct stream URL (expires)
    stream_expires: Optional[datetime] = None  # When stream URL expires
    download_path: Optional[str] = None  # Path to downloaded video file
    quality: Optional[str] = None  # Video quality (e.g., "720p")

    # Database metadata
    added_time: Optional[datetime] = None
    last_played: Optional[datetime] = None
    play_count: int = 0

    # Additional metadata
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def get_display_title(self) -> str:
        """Get the display title for this video."""
        if self.title:
            return self.title
        if self.is_youtube and self.youtube_id:
            return f"YouTube: {self.youtube_id}"
        return os.path.basename(self.path)

    def get_playback_duration(self) -> Optional[float]:
        """Calculate the actual playback duration considering start/end times."""
        if self.duration is None:
            return None

        start = self.custom_start_time or 0.0
        end = self.custom_end_time if self.custom_end_time is not None else self.duration

        return max(0.0, end - start)

    def is_stream_expired(self) -> bool:
        """Check if YouTube stream URL is expired."""
        if not self.is_youtube or not self.stream_expires:
            return False
        return datetime.now() >= self.stream_expires

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)

        # Convert datetime objects to ISO format strings
        if self.stream_expires:
            data["stream_expires"] = self.stream_expires.isoformat()
        if self.added_time:
            data["added_time"] = self.added_time.isoformat()
        if self.last_played:
            data["last_played"] = self.last_played.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VideoEntry":
        """Create VideoEntry from dictionary."""
        # Convert ISO format strings back to datetime objects
        if "stream_expires" in data and isinstance(data["stream_expires"], str):
            try:
                data["stream_expires"] = datetime.fromisoformat(data["stream_expires"])
            except (ValueError, TypeError):
                data["stream_expires"] = None

        if "added_time" in data and isinstance(data["added_time"], str):
            try:
                data["added_time"] = datetime.fromisoformat(data["added_time"])
            except (ValueError, TypeError):
                data["added_time"] = None

        if "last_played" in data and isinstance(data["last_played"], str):
            try:
                data["last_played"] = datetime.fromisoformat(data["last_played"])
            except (ValueError, TypeError):
                data["last_played"] = None

        # Handle tags (might be JSON string in database)
        if "tags" in data and isinstance(data["tags"], str):
            try:
                data["tags"] = json.loads(data["tags"])
            except (json.JSONDecodeError, TypeError):
                data["tags"] = []

        return cls(**data)


class PawVisionDatabase:
    """SQLite database access layer for PawVision video library."""

    def __init__(self, db_path: str = "pawvision.db"):
        """Initialize database connection and schema.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.db_lock = Lock()

        # Ensure database directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Initialize schema
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS videos (
                        path TEXT PRIMARY KEY,
                        title TEXT,
                        custom_start_time REAL DEFAULT 0.0,
                        custom_end_time REAL,
                        duration REAL,
                        size INTEGER,
                        modified_time REAL,
                        is_youtube INTEGER DEFAULT 0,
                        youtube_id TEXT,
                        youtube_url TEXT,
                        stream_url TEXT,
                        stream_expires TEXT,
                        download_path TEXT,
                        quality TEXT,
                        added_time TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_played TEXT,
                        play_count INTEGER DEFAULT 0,
                        tags TEXT,
                        notes TEXT
                    )
                """
                )

                # Create indexes for common queries
                conn.execute("CREATE INDEX IF NOT EXISTS idx_is_youtube ON videos(is_youtube)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_youtube_id ON videos(youtube_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_last_played ON videos(last_played)")

                conn.commit()

            self.logger.info("Video library database initialized: %s", self.db_path)

        except sqlite3.Error as e:
            self.logger.error("Failed to initialize database schema: %s", e)
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def add_or_update_video(self, video_entry: VideoEntry) -> bool:
        """Add a new video or update existing entry.

        Args:
            video_entry: VideoEntry object to add or update

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    # Convert VideoEntry to database row
                    data = {
                        "path": video_entry.path,
                        "title": video_entry.title,
                        "custom_start_time": video_entry.custom_start_time,
                        "custom_end_time": video_entry.custom_end_time,
                        "duration": video_entry.duration,
                        "size": video_entry.size,
                        "modified_time": video_entry.modified_time,
                        "is_youtube": 1 if video_entry.is_youtube else 0,
                        "youtube_id": video_entry.youtube_id,
                        "youtube_url": video_entry.youtube_url,
                        "stream_url": video_entry.stream_url,
                        "stream_expires": video_entry.stream_expires.isoformat()
                        if video_entry.stream_expires
                        else None,
                        "download_path": video_entry.download_path,
                        "quality": video_entry.quality,
                        "added_time": video_entry.added_time.isoformat()
                        if video_entry.added_time
                        else datetime.now().isoformat(),
                        "last_played": video_entry.last_played.isoformat()
                        if video_entry.last_played
                        else None,
                        "play_count": video_entry.play_count,
                        "tags": json.dumps(video_entry.tags) if video_entry.tags else "[]",
                        "notes": video_entry.notes,
                    }

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO videos (
                            path, title, custom_start_time, custom_end_time, duration,
                            size, modified_time, is_youtube, youtube_id, youtube_url,
                            stream_url, stream_expires, download_path, quality,
                            added_time, last_played, play_count, tags, notes
                        ) VALUES (
                            :path, :title, :custom_start_time, :custom_end_time, :duration,
                            :size, :modified_time, :is_youtube, :youtube_id, :youtube_url,
                            :stream_url, :stream_expires, :download_path, :quality,
                            :added_time, :last_played, :play_count, :tags, :notes
                        )
                    """,
                        data,
                    )
                    conn.commit()

            self.logger.debug("Video added/updated: %s", video_entry.path)
            return True

        except sqlite3.Error as e:
            self.logger.error("Failed to add/update video %s: %s", video_entry.path, e)
            return False

    def get_video(self, path: str) -> Optional[VideoEntry]:
        """Get a video entry by path.

        Args:
            path: Video path or youtube:// identifier

        Returns:
            VideoEntry if found, None otherwise
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    cursor = conn.execute("SELECT * FROM videos WHERE path = ?", (path,))
                    row = cursor.fetchone()

                    if row:
                        return self._row_to_video_entry(row)
                    return None

        except sqlite3.Error as e:
            self.logger.error("Failed to get video %s: %s", path, e)
            return None

    def get_all_videos(self) -> List[VideoEntry]:
        """Get all video entries.

        Returns:
            List of VideoEntry objects
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    cursor = conn.execute("SELECT * FROM videos ORDER BY added_time DESC")
                    rows = cursor.fetchall()
                    return [self._row_to_video_entry(row) for row in rows]

        except sqlite3.Error as e:
            self.logger.error("Failed to get all videos: %s", e)
            return []

    def remove_video(self, path: str) -> bool:
        """Remove a video entry from the library.

        Args:
            path: Video path or youtube:// identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    conn.execute("DELETE FROM videos WHERE path = ?", (path,))
                    conn.commit()

            self.logger.debug("Video removed: %s", path)
            return True

        except sqlite3.Error as e:
            self.logger.error("Failed to remove video %s: %s", path, e)
            return False

    def update_stream_url(self, path: str, stream_url: str, stream_expires: datetime) -> bool:
        """Update YouTube stream URL and expiration.

        Args:
            path: Video path (youtube:// identifier)
            stream_url: New stream URL
            stream_expires: When the stream URL expires

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE videos 
                        SET stream_url = ?, stream_expires = ?
                        WHERE path = ?
                    """,
                        (stream_url, stream_expires.isoformat(), path),
                    )
                    conn.commit()

            self.logger.debug("Stream URL updated for: %s", path)
            return True

        except sqlite3.Error as e:
            self.logger.error("Failed to update stream URL for %s: %s", path, e)
            return False

    def record_playback(self, path: str) -> bool:
        """Record that a video was played.

        Args:
            path: Video path or youtube:// identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE videos 
                        SET last_played = ?, play_count = play_count + 1
                        WHERE path = ?
                    """,
                        (datetime.now().isoformat(), path),
                    )
                    conn.commit()

            return True

        except sqlite3.Error as e:
            self.logger.error("Failed to record playback for %s: %s", path, e)
            return False

    def get_youtube_videos(self) -> List[VideoEntry]:
        """Get all YouTube video entries.

        Returns:
            List of YouTube VideoEntry objects
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM videos WHERE is_youtube = 1 ORDER BY added_time DESC"
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_video_entry(row) for row in rows]

        except sqlite3.Error as e:
            self.logger.error("Failed to get YouTube videos: %s", e)
            return []

    def get_local_videos(self) -> List[VideoEntry]:
        """Get all local file video entries.

        Returns:
            List of local file VideoEntry objects
        """
        try:
            with self.db_lock:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM videos WHERE is_youtube = 0 ORDER BY path"
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_video_entry(row) for row in rows]

        except sqlite3.Error as e:
            self.logger.error("Failed to get local videos: %s", e)
            return []

    def _row_to_video_entry(self, row: sqlite3.Row) -> VideoEntry:
        """Convert database row to VideoEntry object.

        Args:
            row: SQLite row object

        Returns:
            VideoEntry object
        """
        # Parse datetime strings
        stream_expires = None
        if row["stream_expires"]:
            try:
                stream_expires = datetime.fromisoformat(row["stream_expires"])
            except (ValueError, TypeError):
                pass

        added_time = None
        if row["added_time"]:
            try:
                added_time = datetime.fromisoformat(row["added_time"])
            except (ValueError, TypeError):
                pass

        last_played = None
        if row["last_played"]:
            try:
                last_played = datetime.fromisoformat(row["last_played"])
            except (ValueError, TypeError):
                pass

        # Parse tags JSON
        tags = []
        if row["tags"]:
            try:
                tags = json.loads(row["tags"])
            except (json.JSONDecodeError, TypeError):
                tags = []

        return VideoEntry(
            path=row["path"],
            title=row["title"],
            custom_start_time=row["custom_start_time"] or 0.0,
            custom_end_time=row["custom_end_time"],
            duration=row["duration"],
            size=row["size"],
            modified_time=row["modified_time"],
            is_youtube=bool(row["is_youtube"]),
            youtube_id=row["youtube_id"],
            youtube_url=row["youtube_url"],
            stream_url=row["stream_url"],
            stream_expires=stream_expires,
            download_path=row["download_path"],
            quality=row["quality"],
            added_time=added_time,
            last_played=last_played,
            play_count=row["play_count"] or 0,
            tags=tags,
            notes=row["notes"],
        )

    def update_video_metadata(
        self,
        path: str,
        title: str = None,
        custom_start_time: float = None,
        custom_end_time: float = None,
    ) -> bool:
        """Update video metadata (title and custom times).

        Args:
            path: Video path or youtube:// identifier
            title: New title (None to keep existing)
            custom_start_time: New start time (None to keep existing)
            custom_end_time: New end time (None to keep existing)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build update query dynamically based on provided parameters
            updates = []
            params = []

            if title is not None:
                updates.append("title = ?")
                params.append(title)

            if custom_start_time is not None:
                updates.append("custom_start_time = ?")
                params.append(custom_start_time)

            if custom_end_time is not None:
                updates.append("custom_end_time = ?")
                params.append(custom_end_time)

            if not updates:
                self.logger.warning("No metadata to update for %s", path)
                return False

            # Add path parameter
            params.append(path)

            with self.db_lock:
                with self._get_connection() as conn:
                    query = f"UPDATE videos SET {', '.join(updates)} WHERE path = ?"
                    conn.execute(query, params)
                    conn.commit()

            self.logger.debug("Metadata updated for: %s", path)
            return True

        except sqlite3.Error as e:
            self.logger.error("Failed to update metadata for %s: %s", path, e)
            return False

    def export_to_json(self, export_path: str) -> bool:
        """Export library to JSON file for backup.

        Args:
            export_path: Path to export JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            videos = self.get_all_videos()
            video_dicts = [video.to_dict() for video in videos]

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": "2.0.0",
                        "export_time": datetime.now().isoformat(),
                        "video_count": len(video_dicts),
                        "videos": video_dicts,
                    },
                    f,
                    indent=2,
                )

            self.logger.info("Library exported to %s (%d videos)", export_path, len(videos))
            return True

        except (OSError, TypeError, ValueError) as e:
            self.logger.error("Failed to export library to %s: %s", export_path, e)
            return False
