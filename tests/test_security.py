import unittest
from unittest.mock import Mock
from pawvision.security import SecurityValidator

class TestSecurityValidator(unittest.TestCase):
    """Test input validation and security."""
    def setUp(self):
        self.validator = SecurityValidator()
    def test_video_file_validation(self):
        valid_file = Mock()
        valid_file.filename = "test_video.mp4"
        valid_file.seek = Mock()
        valid_file.tell = Mock(return_value=1024 * 1024)
        invalid_ext_file = Mock()
        invalid_ext_file.filename = "test_file.txt"
        invalid_ext_file.seek = Mock()
        invalid_ext_file.tell = Mock(return_value=1024)
        valid, result = self.validator.validate_video_file(valid_file)
        self.assertTrue(valid)
        self.assertEqual(result, "test_video.mp4")
        valid, result = self.validator.validate_video_file(invalid_ext_file)
        self.assertFalse(valid)
        self.assertIn("Unsupported file type", result)
    def test_time_format_validation(self):
        self.assertTrue(self.validator.validate_time_format("09:30"))
        self.assertTrue(self.validator.validate_time_format("23:59"))
        self.assertTrue(self.validator.validate_time_format("00:00"))
        self.assertFalse(self.validator.validate_time_format("25:00"))
        self.assertFalse(self.validator.validate_time_format("12:60"))
        self.assertFalse(self.validator.validate_time_format("invalid"))
        self.assertFalse(self.validator.validate_time_format(""))
        self.assertFalse(self.validator.validate_time_format(None))
    def test_integer_range_validation(self):
        valid, error = self.validator.validate_integer_range("50", 0, 100, "Volume")
        self.assertTrue(valid)
        self.assertEqual(error, "")
        valid, error = self.validator.validate_integer_range("150", 0, 100, "Volume")
        self.assertFalse(valid)
        self.assertIn("must be between 0 and 100", error)
        valid, error = self.validator.validate_integer_range("invalid", 0, 100, "Volume")
        self.assertFalse(valid)
        self.assertIn("must be a valid integer", error)
    def test_schedule_validation(self):
        valid, result = self.validator.validate_schedule_list("09:00, 12:30, 18:45")
        self.assertTrue(valid)
        self.assertEqual(result, ["09:00", "12:30", "18:45"])
        valid, result = self.validator.validate_schedule_list("")
        self.assertTrue(valid)
        self.assertEqual(result, [])
        valid, result = self.validator.validate_schedule_list("09:00, 25:00")
        self.assertFalse(valid)
        self.assertIn("Invalid time format: 25:00", result[0])
