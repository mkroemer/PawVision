import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from pawvision.config import PawVisionConfig, ConfigManager
from pawvision.database import VideoEntry
from pawvision.statistics import StatisticsManager
from pawvision.video_player import VideoPlayer
from pawvision.web_interface import WebInterface


class TestPiImprovements(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.stats_file = os.path.join(self.temp_dir, "test_stats.json")
        self.stats_db = os.path.join(self.temp_dir, "test_stats.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_config_defaults_enable_local_first_and_housekeeping(self):
        config = PawVisionConfig()
        self.assertTrue(config.prefer_local_playback)
        self.assertTrue(config.housekeeping_enabled)
        self.assertEqual(config.housekeeping_interval_minutes, 60)

    def test_playback_path_prefers_downloaded_file_for_youtube(self):
        downloaded_file = os.path.join(self.temp_dir, "dQw4w9WgXcQ.mp4")
        Path(downloaded_file).write_bytes(b"test")

        player = VideoPlayer.__new__(VideoPlayer)
        player.prefer_local_playback = True
        player.logger = Mock()
        player.library_manager = Mock()

        entry = VideoEntry(
            path="youtube://dQw4w9WgXcQ",
            is_youtube=True,
            youtube_id="dQw4w9WgXcQ",
            download_path=downloaded_file,
            stream_url="https://stream.example.com/video",
            stream_expires=datetime.now(),
            youtube_url="https://youtube.com/watch?v=dQw4w9WgXcQ",
        )

        playback_path = player._get_playback_path(entry)
        self.assertEqual(playback_path, downloaded_file)

    def test_video_list_supports_pagination_for_lightweight_loading(self):
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
        video_player.get_all_videos = Mock(return_value=[])
        video_player.get_video_library_entries = Mock(
            return_value=[
                VideoEntry(path=f"/videos/video_{idx}.mp4", title=f"Video {idx}", duration=60)
                for idx in range(1, 26)
            ]
        )

        gpio_manager = Mock()
        web_interface = WebInterface(config, video_player, stats_manager, gpio_manager, config_manager)
        client = web_interface.app.test_client()

        response = client.get("/api/video/list?paginated=1&page=2&per_page=10")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["videos"]), 10)
        self.assertEqual(payload["pagination"]["page"], 2)
        self.assertEqual(payload["pagination"]["total"], 25)
        self.assertTrue(payload["pagination"]["has_more"])

    def test_next_endpoint_uses_web_stop_reason_and_success_response(self):
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
        video_player.is_playing = Mock(return_value=True)
        video_player.get_all_videos = Mock(return_value=[])
        video_player.get_video_library_entries = Mock(
            return_value=[
                VideoEntry(path=f"/videos/video_{idx}.mp4", title=f"Video {idx}", duration=60)
                for idx in range(1, 26)
            ]
        )
        video_player.stop_video = Mock(return_value=True)
        video_player.play_random_video = Mock(return_value=True)

        gpio_manager = Mock()
        web_interface = WebInterface(config, video_player, stats_manager, gpio_manager, config_manager)
        client = web_interface.app.test_client()

        response = client.post("/api/next")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        video_player.stop_video.assert_called_once_with(reason="web")
