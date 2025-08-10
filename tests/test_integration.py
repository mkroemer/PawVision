import unittest
import tempfile
import os
from pawvision.main import PawVisionApp
from pawvision.statistics_unified import StatisticsManager

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.stats_file = os.path.join(self.temp_dir, "test_stats.json")
        self.stats_db = os.path.join(self.temp_dir, "test_stats.db")
        self.videos_dir = os.path.join(self.temp_dir, "videos")
        os.makedirs(self.videos_dir)
        self.test_video = os.path.join(self.videos_dir, "test.mp4")
        with open(self.test_video, 'w', encoding='utf-8') as f:
            f.write("fake video content")
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    def test_complete_system_initialization(self):
        app = PawVisionApp(dev_mode=True)
        app.initialize()
        self.assertIsNotNone(app.config_manager)
        self.assertIsNotNone(app.statistics_manager)
        self.assertIsNotNone(app.video_player)
        self.assertIsNotNone(app.gpio_manager)
        self.assertIsNotNone(app.web_interface)
        app.cleanup()
    def test_config_statistics_integration(self):
        stats_manager = StatisticsManager(self.stats_db, enabled=True, legacy_json_file=self.stats_file)
        stats_manager.record_button_press("play")
        stats_manager.record_api_call("status")
        summary = stats_manager.get_summary()
        total_presses = summary.get('button_presses', {}).get('total', 0)
        total_api_calls = summary.get('api_calls', {}).get('total', 0)
        self.assertGreaterEqual(total_presses, 1)
        self.assertGreaterEqual(total_api_calls, 1)
