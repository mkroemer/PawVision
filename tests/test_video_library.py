"""Tests for video library functionality."""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pawvision.video_library import VideoLibraryManager, VideoEntry
from pawvision.database import PawVisionDatabase


class TestVideoLibrary(unittest.TestCase):
    """Test video library management."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_library.db")
        self.library = VideoLibraryManager(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_video_entry_creation(self):
        """Test creating video entries."""
        entry = VideoEntry(
            path="/test/video.mp4",
            title="Test Video",
            custom_start_time=30.0,
            custom_end_time=120.0,
            duration=150.0
        )
        
        self.assertEqual(entry.path, "/test/video.mp4")
        self.assertEqual(entry.title, "Test Video")
        self.assertEqual(entry.custom_start_time, 30.0)
        self.assertEqual(entry.custom_end_time, 120.0)
        self.assertEqual(entry.duration, 150.0)
    
    def test_video_entry_display_title(self):
        """Test video entry display title logic."""
        # With custom title
        entry_with_title = VideoEntry(
            path="/test/video.mp4",
            title="Custom Title",
            duration=100.0
        )
        self.assertEqual(entry_with_title.get_display_title(), "Custom Title")
        
        # Without custom title (should use filename)
        entry_no_title = VideoEntry(
            path="/test/my_video.mp4",
            duration=100.0
        )
        self.assertEqual(entry_no_title.get_display_title(), "my_video.mp4")
    
    def test_video_entry_effective_duration(self):
        """Test effective duration calculation."""
        # With custom times
        entry_custom = VideoEntry(
            path="/test/video.mp4",
            custom_start_time=30.0,
            custom_end_time=120.0,
            duration=150.0
        )
        self.assertEqual(entry_custom.get_effective_duration(), 90.0)
        
        # Without custom times (should use full duration)
        entry_full = VideoEntry(
            path="/test/video.mp4",
            duration=150.0
        )
        self.assertEqual(entry_full.get_effective_duration(), 150.0)
    
    def test_add_and_retrieve_video(self):
        """Test adding and retrieving videos."""
        test_entry = VideoEntry(
            path="/test/video.mp4",
            title="Test Video",
            custom_start_time=30.0,
            custom_end_time=120.0,
            duration=150.0
        )
        
        # Add video
        success = self.library.add_or_update_video(test_entry)
        self.assertTrue(success)
        
        # Retrieve video
        retrieved = self.library.get_video("/test/video.mp4")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.path, "/test/video.mp4")
        self.assertEqual(retrieved.title, "Test Video")
        self.assertEqual(retrieved.custom_start_time, 30.0)
        self.assertEqual(retrieved.custom_end_time, 120.0)
    
    def test_update_video_metadata(self):
        """Test updating video metadata."""
        # Add initial video
        test_entry = VideoEntry(
            path="/test/video.mp4",
            title="Original Title",
            custom_start_time=0.0,
            custom_end_time=100.0,
            duration=150.0
        )
        self.library.add_or_update_video(test_entry)
        
        # Update metadata
        success = self.library.update_video_metadata(
            "/test/video.mp4",
            title="Updated Title",
            custom_start_time=30.0,
            custom_end_time=120.0
        )
        self.assertTrue(success)
        
        # Verify update
        updated = self.library.get_video("/test/video.mp4")
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.custom_start_time, 30.0)
        self.assertEqual(updated.custom_end_time, 120.0)
    
    def test_get_all_videos(self):
        """Test getting all videos."""
        # Add multiple videos
        videos = [
            VideoEntry(path="/test/video1.mp4", title="Video 1", duration=100.0),
            VideoEntry(path="/test/video2.mp4", title="Video 2", duration=200.0),
            VideoEntry(path="/test/video3.mp4", title="Video 3", duration=150.0)
        ]
        
        for video in videos:
            self.library.add_or_update_video(video)
        
        # Get all videos
        all_videos = self.library.get_all_videos()
        self.assertEqual(len(all_videos), 3)
        
        # Verify paths are included
        paths = [v.path for v in all_videos]
        self.assertIn("/test/video1.mp4", paths)
        self.assertIn("/test/video2.mp4", paths)
        self.assertIn("/test/video3.mp4", paths)
    
    def test_get_playable_videos(self):
        """Test getting playable videos."""
        # Create actual temporary video files for this test
        temp_video_dir = os.path.join(self.temp_dir, "videos")
        os.makedirs(temp_video_dir)
        
        # Create dummy video files
        valid1_path = os.path.join(temp_video_dir, "valid1.mp4")
        valid2_path = os.path.join(temp_video_dir, "valid2.mp4")
        invalid_path = os.path.join(temp_video_dir, "invalid.mp4")
        
        for path in [valid1_path, valid2_path, invalid_path]:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("dummy video content")
        
        # Add videos with different configurations
        videos = [
            VideoEntry(path=valid1_path, duration=100.0),
            VideoEntry(path=valid2_path, custom_start_time=30.0, custom_end_time=90.0, duration=120.0),
            VideoEntry(path=invalid_path, custom_start_time=90.0, custom_end_time=30.0, duration=120.0)  # Invalid range
        ]
        
        for video in videos:
            self.library.add_or_update_video(video)
        
        # Get playable videos (should exclude invalid range)
        playable = self.library.get_playable_videos()
        self.assertEqual(len(playable), 2)
        
        # Verify valid videos are included
        paths = [v.path for v in playable]
        self.assertIn(valid1_path, paths)
        self.assertIn(valid2_path, paths)
        self.assertNotIn(invalid_path, paths)
    
    def test_remove_video(self):
        """Test removing videos."""
        # Add video
        test_entry = VideoEntry(path="/test/video.mp4", duration=100.0)
        self.library.add_or_update_video(test_entry)
        
        # Verify it exists
        self.assertIsNotNone(self.library.get_video("/test/video.mp4"))
        
        # Remove video
        success = self.library.remove_video("/test/video.mp4")
        self.assertTrue(success)
        
        # Verify it's gone
        self.assertIsNone(self.library.get_video("/test/video.mp4"))
    
    def test_nonexistent_video_operations(self):
        """Test operations on nonexistent videos."""
        # Try to get nonexistent video
        self.assertIsNone(self.library.get_video("/nonexistent/video.mp4"))
        
        # Try to update nonexistent video (this creates a new entry)
        success = self.library.update_video_metadata("/nonexistent/video.mp4", title="New Title")
        self.assertTrue(success)  # Should succeed by creating new entry
        
        # Verify the entry was created
        created_entry = self.library.get_video("/nonexistent/video.mp4")
        self.assertIsNotNone(created_entry)
        self.assertEqual(created_entry.title, "New Title")
        
        # Try to remove nonexistent video
        success = self.library.remove_video("/truly/nonexistent/video.mp4")
        self.assertFalse(success)
    
    def test_database_persistence(self):
        """Test that data persists across library manager instances."""
        # Add video with first manager
        test_entry = VideoEntry(
            path="/test/persistent.mp4",
            title="Persistent Video",
            duration=100.0
        )
        self.library.add_or_update_video(test_entry)
        
        # Create new manager with same database
        new_library = VideoLibraryManager(self.db_path)
        
        # Verify video exists in new manager
        retrieved = new_library.get_video("/test/persistent.mp4")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Persistent Video")


class TestPawVisionDatabase(unittest.TestCase):
    """Test unified database functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_unified.db")
        self.db = PawVisionDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database initialization creates tables."""
        # Database should be created and initialized
        self.assertTrue(os.path.exists(self.db_path))
        
        # Should be able to add video entries
        entry = VideoEntry(path="/test/video.mp4", duration=100.0)
        success = self.db.add_or_update_video(entry)
        self.assertTrue(success)
        
        # Should be able to retrieve video entries
        retrieved = self.db.get_video("/test/video.mp4")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.path, "/test/video.mp4")
    
    def test_video_crud_operations(self):
        """Test CRUD operations for videos."""
        # Create
        entry = VideoEntry(
            path="/test/crud.mp4",
            title="CRUD Test",
            custom_start_time=10.0,
            custom_end_time=90.0,
            duration=100.0
        )
        self.assertTrue(self.db.add_or_update_video(entry))
        
        # Read
        retrieved = self.db.get_video("/test/crud.mp4")
        self.assertEqual(retrieved.title, "CRUD Test")
        
        # Update
        updated_entry = VideoEntry(
            path="/test/crud.mp4",
            title="Updated CRUD Test",
            custom_start_time=20.0,
            custom_end_time=80.0,
            duration=100.0
        )
        self.assertTrue(self.db.add_or_update_video(updated_entry))
        
        # Verify update
        updated = self.db.get_video("/test/crud.mp4")
        self.assertEqual(updated.title, "Updated CRUD Test")
        self.assertEqual(updated.custom_start_time, 20.0)
        
        # Delete
        self.assertTrue(self.db.remove_video("/test/crud.mp4"))
        self.assertIsNone(self.db.get_video("/test/crud.mp4"))


if __name__ == '__main__':
    unittest.main()
