"""Utility functions for generating and managing video thumbnails."""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional
import urllib.request

logger = logging.getLogger(__name__)


def ensure_thumbnails_dir(base_dir: str = ".") -> str:
    """Ensure thumbnails directory exists and return path."""
    thumbnails_dir = os.path.join(base_dir, "videos", "thumbnails")
    os.makedirs(thumbnails_dir, exist_ok=True)
    return thumbnails_dir


def get_video_duration_ffprobe(video_path: str) -> Optional[float]:
    """
    Get video duration using ffprobe.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        Duration in seconds, or None if unable to determine
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
        logger.debug(f"Could not get duration with ffprobe: {e}")
    
    return None


def generate_video_thumbnail(video_path: str, output_path: str, timestamp: float = 5.0) -> bool:
    """
    Generate a thumbnail from a video file using ffmpeg.
    
    Args:
        video_path: Path to the video file
        output_path: Path where thumbnail should be saved
        timestamp: Time in seconds to capture thumbnail from (default: 5s)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use ffmpeg to generate thumbnail
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-vf', 'scale=320:-1',  # Width 320px, maintain aspect ratio
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            logger.debug(f"Generated thumbnail: {output_path}")
            return True
        else:
            logger.warning(f"Failed to generate thumbnail for {video_path}: {result.stderr.decode()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Thumbnail generation timed out for {video_path}")
        return False
    except FileNotFoundError:
        logger.warning("ffmpeg not found, cannot generate thumbnails")
        return False
    except Exception as e:
        logger.error(f"Error generating thumbnail for {video_path}: {e}")
        return False


def download_youtube_thumbnail(youtube_id: str, output_path: str) -> bool:
    """
    Download thumbnail from YouTube.
    
    Args:
        youtube_id: YouTube video ID
        output_path: Path where thumbnail should be saved
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Try different thumbnail qualities (maxresdefault, hqdefault, mqdefault, default)
        thumbnail_urls = [
            f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg",
            f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg",
            f"https://img.youtube.com/vi/{youtube_id}/mqdefault.jpg",
            f"https://img.youtube.com/vi/{youtube_id}/default.jpg",
        ]
        
        for url in thumbnail_urls:
            try:
                urllib.request.urlretrieve(url, output_path)
                # Check if download was successful and file is not empty
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    logger.debug(f"Downloaded YouTube thumbnail: {output_path}")
                    return True
            except Exception as e:
                logger.debug(f"Failed to download from {url}: {e}")
                continue
        
        logger.warning(f"Could not download thumbnail for YouTube video {youtube_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error downloading YouTube thumbnail for {youtube_id}: {e}")
        return False


def get_thumbnail_path(video_path: str, youtube_id: Optional[str] = None, base_dir: str = ".") -> Optional[str]:
    """
    Get or generate thumbnail for a video.
    
    Args:
        video_path: Path to the video file or youtube:// URI
        youtube_id: YouTube video ID (if applicable)
        base_dir: Base directory for thumbnails
    
    Returns:
        Path to thumbnail if successful, None otherwise
    """
    thumbnails_dir = ensure_thumbnails_dir(base_dir)
    
    # Determine thumbnail filename
    if youtube_id:
        thumbnail_filename = f"yt_{youtube_id}.jpg"
    else:
        # Use video filename without extension
        video_filename = Path(video_path).stem
        thumbnail_filename = f"{video_filename}.jpg"
    
    thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
    
    # If thumbnail already exists, return it
    if os.path.exists(thumbnail_path):
        return thumbnail_path
    
    # Generate thumbnail
    if youtube_id:
        success = download_youtube_thumbnail(youtube_id, thumbnail_path)
    elif os.path.exists(video_path):
        # Get video duration and use middle frame for better thumbnail
        duration = get_video_duration_ffprobe(video_path)
        timestamp = duration / 2.0 if duration and duration > 10 else 5.0
        success = generate_video_thumbnail(video_path, thumbnail_path, timestamp)
    else:
        logger.warning(f"Video file does not exist: {video_path}")
        return None
    
    return thumbnail_path if success else None
