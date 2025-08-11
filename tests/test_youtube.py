#!/usr/bin/env python3
"""Test script for YouTube integration."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pawvision.youtube_manager import YouTubeManager
from pawvision.video_library import VideoLibraryManager
from pawvision.database import VideoEntry

def test_youtube_manager():
    """Test basic YouTube manager functionality."""
    print("Testing YouTube Manager...")
    
    # Initialize manager
    yt_manager = YouTubeManager(
        video_directories=["test_videos"],
        cache_dir="test_youtube_cache",
        preferred_quality="720p"
    )
    
    # Test URL validation
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Valid
        "https://youtu.be/dQw4w9WgXcQ",  # Valid short URL
        "not a url",  # Invalid
        "https://example.com",  # Invalid domain
    ]
    
    for url in test_urls:
        video_id = yt_manager.extract_video_id(url)
        print(f"URL: {url}")
        print(f"Video ID: {video_id}")
        print(f"Valid: {video_id is not None}")
        print()

def test_video_library():
    """Test video library with YouTube integration."""
    print("Testing Video Library with YouTube...")
    
    # Clean slate - remove test database if it exists
    test_db = "test_pawvision.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Initialize library manager
    library = VideoLibraryManager(
        db_path=test_db,
        video_directories=["test_videos"],
        youtube_cache_dir="test_youtube_cache",
        youtube_preferred_quality="720p"
    )
    
    # Test adding a YouTube video (won't actually download/stream)
    print("Testing YouTube video entry creation...")
    video_entry = VideoEntry(
        path="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Test YouTube Video",
        custom_start_time=10.0,
        custom_end_time=120.0,
        is_youtube=True,
        youtube_id="dQw4w9WgXcQ",
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        quality="720p"
    )
    
    # Add to library
    success = library.add_or_update_video(video_entry)
    print(f"Added YouTube video to library: {success}")
    
    # Retrieve it
    retrieved = library.get_video(video_entry.path)
    if retrieved:
        print(f"Retrieved video: {retrieved.get_display_title()}")
        print(f"Is YouTube: {retrieved.is_youtube}")
        print(f"YouTube ID: {retrieved.youtube_id}")
        print(f"Custom range: {retrieved.custom_start_time}s - {retrieved.custom_end_time}s")
        print(f"Effective duration: {retrieved.get_effective_duration()}s")
    
    # List all videos
    all_videos = library.get_all_videos()
    print(f"Total videos in library: {len(all_videos)}")
    
    # Clean up
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("YouTube integration test completed successfully!")

if __name__ == "__main__":
    print("PawVision YouTube Integration Test")
    print("=" * 40)
    
    test_youtube_manager()
    test_video_library()
    
    print("All tests completed!")
