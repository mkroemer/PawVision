import unittest
import tempfile
import os
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from pawvision.config import PawVisionConfig, ConfigManager

class TestPawVisionConfig(unittest.TestCase):
    """Test configuration management."""
    def test_default_config(self):
        config = PawVisionConfig()
        self.assertEqual(config.playback_duration_minutes, 30)
        self.assertEqual(config.post_playback_cooldown_minutes, 5)
        self.assertEqual(config.volume, 50)
        self.assertEqual(config.night_mode_start, "22:00")
        self.assertEqual(config.night_mode_end, "06:00")
        self.assertTrue(config.button_enabled)
        self.assertTrue(config.second_press_stops)
        self.assertEqual(config.button_pin, 17)
        self.assertEqual(config.play_schedule, [])
        self.assertFalse(config.motion_sensor_enabled)
        self.assertFalse(config.motion_stop_enabled)
        self.assertEqual(config.motion_stop_timeout_seconds, 300)
    def test_config_validation(self):
        config = PawVisionConfig(volume=75, playback_duration_minutes=45)
        config.validate()
        with self.assertRaises(ValueError):
            PawVisionConfig(volume=150)
        with self.assertRaises(ValueError):
            PawVisionConfig(playback_duration_minutes=-5)
        with self.assertRaises(ValueError):
            PawVisionConfig(night_mode_start="25:00")
    def test_time_format_validation(self):
        valid_schedule = PawVisionConfig(play_schedule=["09:30", "23:59", "00:00"])
        valid_schedule.validate()
        with self.assertRaises(ValueError):
            PawVisionConfig(play_schedule=["25:00"]).validate()
        with self.assertRaises(ValueError):
            PawVisionConfig(play_schedule=["12:60"]).validate()
        with self.assertRaises(ValueError):
            PawVisionConfig(play_schedule=["invalid"]).validate()
    def test_new_config_fields(self):
        config = PawVisionConfig(
            post_playback_cooldown_minutes=10,
            motion_sensor_enabled=True,
            motion_stop_enabled=True,
            motion_stop_timeout_seconds=600,
            button_disable_start="23:00",
            button_disable_end="07:00"
        )
        config.validate()
        self.assertEqual(config.post_playback_cooldown_minutes, 10)
        self.assertTrue(config.motion_sensor_enabled)
        self.assertTrue(config.motion_stop_enabled)
        self.assertEqual(config.motion_stop_timeout_seconds, 600)
        self.assertEqual(config.button_disable_start, "23:00")
        self.assertEqual(config.button_disable_end, "07:00")
    def test_time_string_validation(self):
        config = PawVisionConfig(
            night_mode_start="22:30",
            night_mode_end="06:30",
            button_disable_start="23:00",
            button_disable_end="07:00"
        )
        config.validate()
        with self.assertRaises(ValueError):
            PawVisionConfig(night_mode_start="25:00").validate()
        with self.assertRaises(ValueError):
            PawVisionConfig(night_mode_end="12:60").validate()
        with self.assertRaises(ValueError):
            PawVisionConfig(button_disable_start="invalid").validate()

class TestConfigManager(unittest.TestCase):
    """Test configuration file management."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        self.config_manager = ConfigManager(self.config_file, dev_mode=True)
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    def test_load_default_config(self):
        config = self.config_manager.load_config()
        self.assertIsInstance(config, PawVisionConfig)
        self.assertEqual(config.playback_duration_minutes, 30)
        self.assertTrue(os.path.exists(self.config_file))
    def test_load_existing_config(self):
        test_config = {
            "playback_duration_minutes": 45,
            "volume": 75,
            "button_enabled": False
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        config = self.config_manager.load_config()
        self.assertEqual(config.playback_duration_minutes, 45)
        self.assertEqual(config.volume, 75)
        self.assertFalse(config.button_enabled)
    def test_save_config(self):
        config = PawVisionConfig(playback_duration_minutes=60, volume=80)
        self.config_manager.save_config(config)
        self.assertTrue(os.path.exists(self.config_file))
        with open(self.config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data['playback_duration_minutes'], 60)
        self.assertEqual(saved_data['volume'], 80)
    def test_invalid_config_handling(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        config = self.config_manager.load_config()
        self.assertEqual(config.playback_duration_minutes, 30)
        backup_file = f"{self.config_file}.backup"
        self.assertTrue(os.path.exists(backup_file))
