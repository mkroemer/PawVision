import unittest
import tempfile
import os
import sys
import shutil
from unittest.mock import Mock
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from pawvision.web_interface import WebInterface
from pawvision.config import ConfigManager
from pawvision.statistics_unified import StatisticsManager
from pawvision.video_player import VideoPlayer

class TestWebInterface(unittest.TestCase):
    """Test web interface functionality."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.stats_file = os.path.join(self.temp_dir, "test_stats.json")
        self.stats_db = os.path.join(self.temp_dir, "test_stats.db")
        self.config_manager = ConfigManager(self.config_file, dev_mode=True)
        self.config = self.config_manager.load_config()
        self.stats_manager = StatisticsManager(self.stats_db, enabled=True, legacy_json_file=self.stats_file)
        self.video_player = Mock()
        self.video_player.video_files = []
        self.video_player.current_video = None
        self.video_player.is_playing = Mock(return_value=False)
        self.video_player.get_all_videos = Mock(return_value=[])
        self.video_player.is_night_mode = Mock(return_value=False)
        self.video_player.play_random_video = Mock(return_value=True)
        self.video_player.stop_video = Mock(return_value=True)
        self.gpio_manager = Mock()
        self.gpio_manager.is_button_allowed = Mock(return_value=True)
        self.gpio_manager.get_next_scheduled_play = Mock(return_value=None)
        self.web_interface = WebInterface(
            config=self.config,
            video_player=self.video_player,
            statistics_manager=self.stats_manager,
            gpio_manager=self.gpio_manager,
            config_manager=self.config_manager
        )
        self.client = self.web_interface.app.test_client()
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    def test_api_health_endpoint(self):
        self.stats_manager.get_summary = Mock(return_value={
            'total_button_presses': 5,
            'total_video_plays': 3,
            'total_api_calls': 2
        })
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status', data)
        self.assertIn('version', data)
        self.assertEqual(data['status'], 'healthy')
    def test_api_status_endpoint(self):
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('is_playing', data)
        self.assertIn('video_count', data)
        self.assertFalse(data['is_playing'])
    def test_api_play_endpoint(self):
        response = self.client.post('/api/play')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'playing')
    def test_api_stop_endpoint(self):
        response = self.client.post('/api/stop')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'stopped')
