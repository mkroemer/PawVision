import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from pawvision.config import ConfigManager
from pawvision.statistics import StatisticsManager
from pawvision.web_interface import WebInterface


class TestIssueFixRegressions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.stats_file = os.path.join(self.temp_dir, "test_stats.json")
        self.stats_db = os.path.join(self.temp_dir, "test_stats.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _create_web_interface(self):
        config_manager = ConfigManager(self.config_file, dev_mode=True)
        config = config_manager.load_config()
        stats_manager = StatisticsManager(
            stats_file=self.stats_file,
            db_file=self.stats_db,
            enabled=True,
        )
        video_player = Mock()
        video_player.video_files = []
        video_player.video_dirs = [self.temp_dir]
        video_player.current_video = None
        video_player.is_playing = Mock(return_value=False)
        video_player.get_video_library_entries = Mock(return_value=[])
        video_player.get_all_videos = Mock(return_value=[])
        gpio_manager = Mock()
        return WebInterface(config, video_player, stats_manager, gpio_manager, config_manager)

    def test_summary_includes_nested_and_legacy_totals(self):
        stats_manager = StatisticsManager(
            stats_file=self.stats_file,
            db_file=self.stats_db,
            enabled=True,
        )
        stats_manager.record_button_press("play", force=True)
        stats_manager.record_api_call("status")

        summary = stats_manager.get_summary()
        self.assertGreaterEqual(summary["button_presses"]["total"], 1)
        self.assertGreaterEqual(summary["api_calls"]["total"], 1)
        self.assertEqual(summary["button_presses"]["total"], summary["total_button_presses"])
        self.assertEqual(summary["api_calls"]["total"], summary["total_api_calls"])

    def test_web_interface_secret_key_uses_environment(self):
        os.environ["PAWVISION_SECRET_KEY"] = "test-secret-key-from-env"
        try:
            web_interface = self._create_web_interface()
            self.assertEqual(web_interface.app.config["SECRET_KEY"], "test-secret-key-from-env")
        finally:
            del os.environ["PAWVISION_SECRET_KEY"]

    def test_web_interface_can_be_initialized_multiple_times(self):
        self._create_web_interface()
        self._create_web_interface()
