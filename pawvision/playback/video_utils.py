"""Video utility functions for duration detection and format handling."""

import logging
import os
import subprocess
from typing import Optional


logger = logging.getLogger(__name__)


def get_video_duration(file_path: str, library_manager=None, video_entry=None) -> Optional[float]:
    """Get video duration in seconds using mediainfo with database caching.
    
    Args:
        file_path: Path to the video file
        library_manager: Optional VideoLibraryManager for caching
        video_entry: Optional existing VideoEntry for cache checking
        
    Returns:
        Duration in seconds, or None if unable to determine
    """
    if not os.path.exists(file_path):
        logger.warning("Video file not found: %s", file_path)
        return None

    # Check database cache first if available
    if library_manager and video_entry:
        if video_entry.duration is not None:
            # Verify the cached duration is still valid (file hasn't been modified)
            try:
                current_mtime = os.path.getmtime(file_path)
                if video_entry.modified_time and abs(current_mtime - video_entry.modified_time) < 1.0:
                    logger.debug("Using cached duration for %s", os.path.basename(file_path))
                    return video_entry.duration
            except OSError:
                pass

    # Try to get duration using available tools
    duration_sec = None
    
    # Method 1: Try ffprobe (most reliable)
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        
        if result.returncode == 0 and result.stdout.strip():
            duration_sec = float(result.stdout.strip())
            logger.debug("Got duration using ffprobe: %.1f seconds", duration_sec)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
        logger.debug("ffprobe not available or failed: %s", e)
    
    # Method 2: Try mediainfo (fallback)
    if duration_sec is None:
        try:
            result = subprocess.run(
                ["mediainfo", "--Inform=Video;%Duration%", file_path],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            
            if result.returncode == 0 and result.stdout.strip():
                duration_ms = int(result.stdout.strip())
                duration_sec = duration_ms / 1000.0
                logger.debug("Got duration using mediainfo: %.1f seconds", duration_sec)
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            logger.debug("mediainfo not available or failed: %s", e)
    
    # Method 3: Use Python library as last resort
    if duration_sec is None:
        try:
            # Try to use moviepy if available
            from moviepy.editor import VideoFileClip
            with VideoFileClip(file_path) as clip:
                duration_sec = clip.duration
            logger.debug("Got duration using moviepy: %.1f seconds", duration_sec)
        except ImportError:
            logger.debug("moviepy not available")
        except Exception as e:
            logger.debug("moviepy failed: %s", e)
    
    # If still no duration, return None
    if duration_sec is None:
        logger.warning("Could not determine duration for %s (no tools available)", file_path)
        return None

    # Update the database with the duration and current mtime if available
    if library_manager:
        try:
            from ..database import VideoEntry
            
            mtime = os.path.getmtime(file_path)
            if video_entry:
                video_entry.duration = duration_sec
                video_entry.modified_time = mtime
                library_manager.add_or_update_video(video_entry)
            else:
                # Create new entry if it doesn't exist
                new_entry = VideoEntry(
                    path=file_path,
                    duration=duration_sec,
                    modified_time=mtime
                )
                library_manager.add_or_update_video(new_entry)
        except OSError as e:
            logger.error("Error updating duration cache in database: %s", e)

    logger.debug(
        "Got duration for %s: %.1f seconds",
        os.path.basename(file_path),
        duration_sec,
    )
    return duration_sec


def format_duration(duration: float) -> str:
    """Format duration in seconds to readable string.
    
    Args:
        duration: Duration in seconds
        
    Returns:
        Formatted string like "1m 30s" or "1h 15m"
    """
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


def detect_video_format(file_path: str) -> Optional[str]:
    """Detect video format/codec using mediainfo.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Format string (e.g., "H.264", "VP9"), or None if unable to determine
    """
    if not os.path.exists(file_path):
        logger.warning("Video file not found: %s", file_path)
        return None

    try:
        result = subprocess.run(
            ["mediainfo", "--Inform=Video;%Format%", file_path],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        return None

    except (subprocess.TimeoutExpired, OSError) as e:
        logger.error("Error detecting video format for %s: %s", file_path, e)
        return None


def validate_video_file(file_path: str) -> bool:
    """Validate that a file is a supported video file.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file exists and has supported extension
    """
    supported_extensions = (".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm")
    
    if not os.path.exists(file_path):
        return False
    
    if not os.path.isfile(file_path):
        return False
    
    return file_path.lower().endswith(supported_extensions)
