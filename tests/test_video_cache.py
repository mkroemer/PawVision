import unittest
import tempfile
import os
import shutil
from pawvision.video_player import VideoCache

class TestVideoCache(unittest.TestCase):
    """Test video duration caching."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "test_cache.json")
        self.cache = VideoCache(self.cache_file, enabled=True)
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    def test_cache_operations(self):
        test_file = os.path.join(self.temp_dir, "test_video.mp4")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("test content")
        duration = self.cache.get_duration(test_file)
        self.assertIsNone(duration)
        self.cache.set_duration(test_file, 120.5)
        duration = self.cache.get_duration(test_file)
        self.assertEqual(duration, 120.5)
    def test_cache_persistence(self):
        test_file = os.path.join(self.temp_dir, "test_video.mp4")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("test content")
        self.cache.set_duration(test_file, 95.0)
        new_cache = VideoCache(self.cache_file, enabled=True)
        duration = new_cache.get_duration(test_file)
        self.assertEqual(duration, 95.0)
    def test_disabled_cache(self):
        disabled_cache = VideoCache(self.cache_file, enabled=False)
        test_file = os.path.join(self.temp_dir, "test_video.mp4")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("test content")
        duration = disabled_cache.get_duration(test_file)
        self.assertIsNone(duration)
        disabled_cache.set_duration(test_file, 100.0)
        self.assertFalse(os.path.exists(self.cache_file))
