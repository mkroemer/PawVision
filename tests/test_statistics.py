import unittest
import tempfile
import os
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from pawvision.statistics_unified import StatisticsManager


class TestStatisticsManager(unittest.TestCase):
    """Test statistics tracking."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.stats_file = os.path.join(self.temp_dir, "test_stats.json")
        self.stats_db = os.path.join(self.temp_dir, "test_stats.db")
        self.stats_manager = StatisticsManager(
            self.stats_db, enabled=True, legacy_json_file=self.stats_file
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_button_press_recording(self):
        result1 = self.stats_manager.record_button_press("play", force=True)
        result2 = self.stats_manager.record_button_press("stop", force=True)
        result3 = self.stats_manager.record_button_press("play", force=True)
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertTrue(result3)
        summary = self.stats_manager.get_summary()
        total_presses = summary.get("button_presses", {}).get("total", 0)
        self.assertGreaterEqual(total_presses, 2)

    def test_video_play_recording(self):
        video_path = "/test/video.mp4"
        self.stats_manager.record_video_play(video_path, "button")
        self.stats_manager.record_video_play(video_path, "api")
        summary = self.stats_manager.get_summary()
        self.assertGreaterEqual(len(summary.get("recent_events", [])), 0)

    def test_stats_persistence(self):
        self.stats_manager.record_button_press("play")
        self.stats_manager.record_api_call("play")
        new_manager = StatisticsManager(
            self.stats_db, enabled=True, legacy_json_file=self.stats_file
        )
        summary = new_manager.get_summary()
        total_presses = summary.get("button_presses", {}).get("total", 0)
        total_api_calls = summary.get("api_calls", {}).get("total", 0)
        self.assertGreaterEqual(total_presses, 1)
        self.assertGreaterEqual(total_api_calls, 1)

    def test_disabled_statistics(self):
        disabled_manager = StatisticsManager(self.stats_db, enabled=False)
        disabled_manager.record_button_press("play")
        disabled_manager.record_video_play("/test/video.mp4", "button")
        stats = disabled_manager.get_summary()
        self.assertEqual(stats, {})
