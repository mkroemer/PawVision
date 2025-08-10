"""Time utilities for PawVision - centralized time parsing and conversion."""

from typing import Tuple, Optional
from datetime import datetime
import logging


class TimeParser:
    """Centralized time parsing and conversion utilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_time_value(self, time_value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        """Parse time value (HH:MM string) to (hour, minute).
        
        Args:
            time_value: String in HH:MM format, or None
            
        Returns:
            Tuple of (hour, minute) or (None, None) if invalid
        """
        if time_value is None:
            return None, None
        
        if isinstance(time_value, str):
            # HH:MM string format
            try:
                parts = time_value.split(':')
                if len(parts) != 2:
                    raise ValueError(f"Invalid time format: {time_value}")
                
                hour, minute = map(int, parts)
                
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError(f"Hour or minute out of range: {hour}:{minute}")
                
                return hour, minute
            except (ValueError, AttributeError) as e:
                self.logger.warning("Invalid time format: %s, error: %s, defaulting to 0:00", time_value, e)
                return 0, 0
        else:
            self.logger.warning("Time value must be a string in HH:MM format, got %s, defaulting to 0:00", type(time_value))
            return 0, 0
    
    def time_to_minutes(self, hour: int, minute: int) -> int:
        """Convert hour and minute to total minutes since midnight.
        
        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
            
        Returns:
            Total minutes since midnight
        """
        return hour * 60 + minute
    
    def parse_to_minutes(self, time_value: Optional[str]) -> Optional[int]:
        """Parse time value and convert directly to minutes since midnight.
        
        Args:
            time_value: String in HH:MM format, or None
            
        Returns:
            Minutes since midnight, or None if time_value is None
        """
        hour, minute = self.parse_time_value(time_value)
        if hour is None:
            return None
        return self.time_to_minutes(hour, minute)
    
    def format_time(self, time_value: Optional[str]) -> str:
        """Format time value for display.
        
        Args:
            time_value: String in HH:MM format, or None
            
        Returns:
            Formatted time string in HH:MM format
        """
        hour, minute = self.parse_time_value(time_value)
        if hour is None:
            return ""
        return f"{hour:02d}:{minute:02d}"
    
    def is_time_in_range(self, start_time: Optional[str], 
                        end_time: Optional[str],
                        current_time: Optional[datetime] = None) -> bool:
        """Check if current time is within the specified range.
        
        Args:
            start_time: Start time (HH:MM string)
            end_time: End time (HH:MM string)
            current_time: Time to check (defaults to now)
            
        Returns:
            True if current time is in range, False otherwise
        """
        if start_time is None or end_time is None:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        current_minutes = self.time_to_minutes(current_time.hour, current_time.minute)
        start_minutes = self.parse_to_minutes(start_time)
        end_minutes = self.parse_to_minutes(end_time)
        
        if start_minutes is None or end_minutes is None:
            return False
        
        if start_minutes < end_minutes:
            # Normal range (e.g., 9:00-17:30)
            return start_minutes <= current_minutes < end_minutes
        else:
            # Overnight range (e.g., 22:30-6:15)
            return current_minutes >= start_minutes or current_minutes < end_minutes


# Global instance for use throughout the application
time_parser = TimeParser()
