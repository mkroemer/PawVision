"""YouTube integration for PawVision video library."""

import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import yt_dlp
    from yt_dlp.utils import DownloadError, ExtractorError
    YT_DLP_AVAILABLE = True
except ImportError:
    yt_dlp = None
    DownloadError = Exception
    ExtractorError = Exception
    YT_DLP_AVAILABLE = False

from .database import VideoEntry


class YouTubeManager:
    """Manages YouTube video integration with streaming and caching capabilities."""
    
    def __init__(self, video_directories: List[str], 
                 cache_dir: str = "youtube_cache",
                 preferred_quality: str = "720p"):
        self.video_directories = video_directories
        self.cache_dir = cache_dir
        self.preferred_quality = preferred_quality
        self.logger = logging.getLogger(__name__)
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        if not YT_DLP_AVAILABLE:
            self.logger.warning("yt-dlp not available. YouTube functionality will be limited.")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        # Handle various YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If URL is already just a video ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
        
        return None
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information from YouTube."""
        if not YT_DLP_AVAILABLE:
            return None
        
        video_id = self.extract_video_id(url)
        if not video_id:
            return None
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", 
                                      download=False)
                
                return {
                    'id': video_id,
                    'title': info.get('title', f'YouTube Video {video_id}'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count'),
                    'formats': info.get('formats', [])
                }
        
        except Exception as e:
            self.logger.error("Error extracting video info for %s: %s", video_id, e)
            return None
    
    def get_video_title_and_duration(self, url: str) -> Tuple[Optional[str], Optional[int]]:
        """Quick method to get just title and duration for URL validation."""
        info = self.get_video_info(url)
        if info:
            return info.get('title'), info.get('duration')
        return None, None
    
    def get_stream_url(self, video_id: str, quality: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Get direct stream URL for a YouTube video."""
        if not YT_DLP_AVAILABLE:
            return None, None
        
        quality = quality or self.preferred_quality
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': self._get_format_selector(quality),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", 
                                      download=False)
                
                # Get the best format URL
                if 'url' in info:
                    # Calculate expiration time (YouTube URLs typically expire in 6 hours)
                    expires = datetime.now() + timedelta(hours=6)
                    return info['url'], expires.isoformat()
        
        except (DownloadError, ExtractorError) as e:
            self.logger.error("Error getting stream URL for %s: %s", video_id, e)
        
        return None, None
    
    def _get_format_selector(self, quality: str) -> str:
        """Get yt-dlp format selector for desired quality."""
        quality_map = {
            '144p': 'worst[height<=144]',
            '240p': 'worst[height<=240]',
            '360p': 'best[height<=360]',
            '480p': 'best[height<=480]',
            '720p': 'best[height<=720]',
            '1080p': 'best[height<=1080]',
            'best': 'best',
            'worst': 'worst'
        }
        
        return quality_map.get(quality, 'best[height<=720]')
    
    def download_video(self, video_id: str, quality: str = None, progress_callback=None) -> Optional[str]:
        """Download YouTube video for offline playback."""
        if not YT_DLP_AVAILABLE:
            return None
        
        quality = quality or self.preferred_quality
        
        # Use the first video directory for downloads
        download_dir = self.video_directories[0] if self.video_directories else "./videos"
        os.makedirs(download_dir, exist_ok=True)
        
        output_path = os.path.join(download_dir, f"{video_id}.%(ext)s")
        
        def progress_hook(d):
            """Progress callback for yt-dlp."""
            if progress_callback and d['status'] == 'downloading':
                try:
                    # Calculate percentage
                    if 'total_bytes' in d:
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d['total_bytes']
                        percentage = (downloaded / total) * 100
                    elif 'total_bytes_estimate' in d:
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d['total_bytes_estimate']
                        percentage = (downloaded / total) * 100
                    else:
                        percentage = 0
                    
                    # Get speed and ETA if available
                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)
                    
                    progress_callback({
                        'status': 'downloading',
                        'percentage': min(100, max(0, percentage)),
                        'downloaded_bytes': d.get('downloaded_bytes', 0),
                        'total_bytes': d.get('total_bytes') or d.get('total_bytes_estimate', 0),
                        'speed': speed,
                        'eta': eta
                    })
                except (TypeError, ZeroDivisionError, KeyError):
                    # Fallback for incomplete progress data
                    progress_callback({
                        'status': 'downloading',
                        'percentage': 0,
                        'downloaded_bytes': 0,
                        'total_bytes': 0,
                        'speed': 0,
                        'eta': 0
                    })
            elif progress_callback and d['status'] == 'finished':
                progress_callback({
                    'status': 'finished',
                    'percentage': 100,
                    'filename': d.get('filename', ''),
                    'total_bytes': d.get('total_bytes', 0)
                })
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': self._get_format_selector(quality),
                'outtmpl': output_path,
                'writeinfojson': False,
                'progress_hooks': [progress_hook] if progress_callback else []
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
            # Find the downloaded file (extension may vary)
            download_dir = self.video_directories[0] if self.video_directories else "./videos"
            for file in os.listdir(download_dir):
                if file.startswith(video_id + "."):
                    download_path = os.path.join(download_dir, file)
                    self.logger.info("Downloaded YouTube video: %s", download_path)
                    return download_path
        
        except (OSError, RuntimeError) as e:
            self.logger.error("Error downloading video %s: %s", video_id, e)
            if progress_callback:
                progress_callback({
                    'status': 'error',
                    'error': str(e)
                })
        
        return None
    
    def create_video_entry(self, url: str, custom_title: str = None,
                          custom_start_time: float = 0.0,
                          custom_end_offset: float = None,  # Changed from custom_end_time to custom_end_offset
                          quality: str = None,
                          download: bool = False) -> Optional[VideoEntry]:
        """Create a VideoEntry for a YouTube video."""
        video_id = self.extract_video_id(url)
        if not video_id:
            self.logger.error("Invalid YouTube URL: %s", url)
            return None
        
        # Get video info
        info = self.get_video_info(url)
        if not info:
            self.logger.error("Could not extract video info for: %s", url)
            return None
        
        # Calculate absolute end time from relative offset
        duration = info.get('duration')
        custom_end_time = None
        if custom_end_offset is not None and duration:
            custom_end_time = max(0, duration - custom_end_offset)
        
        # Get stream URL
        stream_url, stream_expires = self.get_stream_url(video_id, quality)
        
        # Download if requested
        download_path = None
        if download:
            download_path = self.download_video(video_id, quality)
        
        # Create video entry
        entry = VideoEntry(
            path=f"youtube://{video_id}",  # Use custom scheme for YouTube videos
            title=custom_title or info.get('title'),
            custom_start_time=custom_start_time,
            custom_end_time=custom_end_time,
            duration=duration,
            is_youtube=True,
            youtube_id=video_id,
            youtube_url=url,
            stream_url=stream_url,
            stream_expires=stream_expires,
            download_path=download_path,
            quality=quality or self.preferred_quality
        )
        
        self.logger.info("Created YouTube video entry: %s", entry.get_display_title())
        return entry
    
    def refresh_stream_url(self, video_entry: VideoEntry) -> bool:
        """Refresh expired stream URL for a YouTube video."""
        if not video_entry.is_youtube or not video_entry.youtube_id:
            return False
        
        stream_url, stream_expires = self.get_stream_url(video_entry.youtube_id, 
                                                        video_entry.quality)
        if stream_url:
            video_entry.stream_url = stream_url
            video_entry.stream_expires = stream_expires
            video_entry.updated_at = datetime.now().isoformat()
            return True
        
        return False
    
    def cleanup_expired_downloads(self, max_age_days: int = 30):
        """Clean up old downloaded YouTube videos."""
        for video_dir in self.video_directories:
            if not os.path.exists(video_dir):
                continue
            
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            cleaned_count = 0
            
            for filename in os.listdir(video_dir):
                # Only clean up YouTube videos (those with 11-character IDs)
                if re.match(r'^[a-zA-Z0-9_-]{11}\.\w+$', filename):
                    filepath = os.path.join(video_dir, filename)
                    
                    try:
                        if os.path.isfile(filepath):
                            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                            if file_time < cutoff_time:
                                os.remove(filepath)
                                cleaned_count += 1
                                self.logger.debug("Cleaned up old download: %s", filename)
                    except OSError as e:
                        self.logger.error("Error cleaning up %s: %s", filename, e)
            
            if cleaned_count > 0:
                self.logger.info("Cleaned up %d old YouTube downloads in %s", cleaned_count, video_dir)
    
    def get_available_qualities(self, video_id: str) -> List[str]:
        """Get available quality options for a YouTube video."""
        if not YT_DLP_AVAILABLE:
            return ['720p']  # Default fallback
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'listformats': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", 
                                      download=False)
                
                qualities = set()
                for fmt in info.get('formats', []):
                    if fmt.get('height'):
                        qualities.add(f"{fmt['height']}p")
                
                # Return sorted list with most common qualities
                available = ['144p', '240p', '360p', '480p', '720p', '1080p']
                return [q for q in available if q in qualities]
        
        except (OSError, RuntimeError) as e:
            self.logger.error("Error getting qualities for %s: %s", video_id, e)
        
        return ['720p']  # Default fallback
