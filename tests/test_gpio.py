import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock
from pawvision.gpio_handler import ButtonHandler
from pawvision.config import ConfigManager

class TestGPIOIntegration(unittest.TestCase):
    """Test GPIO integration with mocks."""
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    def test_gpio_manager_initialization(self):
        config_manager = ConfigManager(self.config_file, dev_mode=True)
        config = config_manager.load_config()
        config.dev_mode = True
        gpio_manager = ButtonHandler(
            config=config,
            video_player=Mock()
        )
        self.assertIsNotNone(gpio_manager)
    def test_button_callback_simulation(self):
        config_manager = ConfigManager(self.config_file, dev_mode=True)
        config = config_manager.load_config()
        config.dev_mode = True
        mock_video_player = Mock()
        mock_video_player.play_random_video = Mock(return_value=True)
        gpio_manager = ButtonHandler(
            config=config,
            video_player=mock_video_player
        )
        self.assertIsNotNone(gpio_manager)
        self.assertTrue(hasattr(gpio_manager, '_handle_button_press'))
        try:
            gpio_manager._handle_button_press()
        except Exception as e:
            self.fail(f"Button press handler raised exception: {e}")
