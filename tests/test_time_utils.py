import unittest
from pawvision.time_utils import TimeParser

class TestTimeUtils(unittest.TestCase):
    """Test time utility functions."""
    def setUp(self):
        self.time_parser = TimeParser()
    def test_parse_time_string(self):
        hour, minute = self.time_parser.parse_time_value("09:30")
        self.assertEqual(hour, 9)
        self.assertEqual(minute, 30)
        hour, minute = self.time_parser.parse_time_value("23:59")
        self.assertEqual(hour, 23)
        self.assertEqual(minute, 59)
        hour, minute = self.time_parser.parse_time_value("00:00")
        self.assertEqual(hour, 0)
        self.assertEqual(minute, 0)
    def test_invalid_time_string(self):
        hour, minute = self.time_parser.parse_time_value("25:00")
        self.assertEqual(hour, 0)
        self.assertEqual(minute, 0)
        hour, minute = self.time_parser.parse_time_value("12:60")
        self.assertEqual(hour, 0)
        self.assertEqual(minute, 0)
        hour, minute = self.time_parser.parse_time_value("invalid")
        self.assertEqual(hour, 0)
        self.assertEqual(minute, 0)
        hour, minute = self.time_parser.parse_time_value("")
        self.assertEqual(hour, 0)
        self.assertEqual(minute, 0)
        hour, minute = self.time_parser.parse_time_value(None)
        self.assertIsNone(hour)
        self.assertIsNone(minute)
    def test_time_to_minutes(self):
        self.assertEqual(self.time_parser.time_to_minutes(9, 30), 570)
        self.assertEqual(self.time_parser.time_to_minutes(0, 0), 0)
        self.assertEqual(self.time_parser.time_to_minutes(23, 59), 1439)
