"""Input validation and security utilities for PawVision."""

import os
import logging
from typing import Tuple, Set
from werkzeug.utils import secure_filename


class SecurityValidator:
    """Handles input validation and security checks."""
    
    ALLOWED_VIDEO_EXTENSIONS: Set[str] = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm'}
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB
    MAX_FILENAME_LENGTH: int = 255
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_video_file(self, file) -> Tuple[bool, str]:
        """Validate uploaded video file.
        
        Args:
            file: Werkzeug FileStorage object
            
        Returns:
            Tuple of (is_valid, message_or_filename)
        """
        if not file or not file.filename:
            return False, "No file selected"
        
        # Secure the filename
        original_filename = file.filename
        filename = secure_filename(original_filename)
        
        if not filename:
            return False, "Invalid filename"
        
        if len(filename) > self.MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {self.MAX_FILENAME_LENGTH} characters)"
        
        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.ALLOWED_VIDEO_EXTENSIONS:
            allowed_exts = ', '.join(sorted(self.ALLOWED_VIDEO_EXTENSIONS))
            return False, f"Unsupported file type: {ext}. Allowed: {allowed_exts}"
        
        # Check file size if possible
        try:
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)     # Seek back to start
            
            if size > self.MAX_FILE_SIZE:
                size_mb = size / (1024 * 1024)
                max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                return False, f"File too large: {size_mb:.1f}MB > {max_mb}MB"
        except (OSError, AttributeError) as e:
            self.logger.warning("Could not check file size: %s", e)
        
        return True, filename
    
    def validate_file_path(self, file_path: str, allowed_directories: list) -> bool:
        """Validate that file path is within allowed directories.
        
        Args:
            file_path: Path to validate
            allowed_directories: List of allowed base directories
            
        Returns:
            True if path is safe, False otherwise
        """
        if not file_path:
            return False
        
        try:
            # Resolve the absolute path
            abs_path = os.path.abspath(file_path)
            
            # Check if path exists and is a file
            if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
                return False
            
            # Check if the file is within allowed directories
            for allowed_dir in allowed_directories:
                abs_allowed_dir = os.path.abspath(allowed_dir)
                if abs_path.startswith(abs_allowed_dir + os.sep):
                    return True
            
            return False
            
        except (OSError, ValueError):
            return False
    
    def validate_time_format(self, time_str: str) -> bool:
        """Validate HH:MM time format.
        
        Args:
            time_str: Time string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not time_str or not isinstance(time_str, str):
            return False
        
        try:
            parts = time_str.strip().split(':')
            if len(parts) != 2:
                return False
            
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
            
        except (ValueError, AttributeError):
            return False
    
    def parse_time_to_hour(self, time_str: str) -> int:
        """Parse time string to hour integer.
        
        Args:
            time_str: Time string in HH:MM format
            
        Returns:
            Hour as integer (0-23)
        """
        if not time_str:
            return None
        
        try:
            parts = time_str.strip().split(':')
            return int(parts[0])
        except (ValueError, AttributeError, IndexError):
            return None

    def validate_schedule_list(self, schedule_str: str) -> Tuple[bool, list]:
        """Validate and parse schedule string.
        
        Args:
            schedule_str: Comma-separated time string
            
        Returns:
            Tuple of (is_valid, parsed_schedule_list)
        """
        if not schedule_str:
            return True, []
        
        try:
            times = [t.strip() for t in schedule_str.split(',') if t.strip()]
            valid_times = []
            
            for time_str in times:
                if self.validate_time_format(time_str):
                    valid_times.append(time_str)
                else:
                    return False, [f"Invalid time format: {time_str}"]
            
            return True, valid_times
            
        except (ValueError, AttributeError, TypeError) as e:
            self.logger.error("Error parsing schedule: %s", e)
            return False, ["Error parsing schedule"]
    
    def validate_integer_range(self, value, min_val: int, max_val: int, name: str) -> Tuple[bool, str]:
        """Validate integer within range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            name: Name of the parameter for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            int_val = int(value)
            if min_val <= int_val <= max_val:
                return True, ""
            else:
                return False, f"{name} must be between {min_val} and {max_val}"
        except ValueError:
            return False, f"{name} must be a valid integer"
    
    def validate_hour(self, value) -> Tuple[bool, int, str]:
        """Validate hour value (0-23).
        
        Args:
            value: Hour value to validate
            
        Returns:
            Tuple of (is_valid, hour_value, error_message)
        """
        try:
            hour = int(value)
            if 0 <= hour <= 23:
                return True, hour, ""
            else:
                return False, 0, "Hour must be between 0 and 23"
        except ValueError:
            return False, 0, "Hour must be a valid integer"
    
    def sanitize_settings_update(self, form_data: dict) -> Tuple[bool, dict, list]:
        """Sanitize and validate settings update form data.
        
        Args:
            form_data: Raw form data dictionary
            
        Returns:
            Tuple of (is_valid, sanitized_data, error_messages)
        """
        errors = []
        sanitized = {}
        
        # Validate playback duration (backward compatibility with timeout)
        if 'playback_duration' in form_data:
            valid, error = self.validate_integer_range(
                form_data['playback_duration'], 1, 180, 'Playback duration'
            )
            if valid:
                sanitized['playback_duration_minutes'] = int(form_data['playback_duration'])
            else:
                errors.append(error)
        elif 'timeout' in form_data:  # Backward compatibility
            valid, error = self.validate_integer_range(
                form_data['timeout'], 1, 180, 'Timeout'
            )
            if valid:
                sanitized['playback_duration_minutes'] = int(form_data['timeout'])
            else:
                errors.append(error)
        
        # Validate post-playback cooldown
        if 'post_playback_cooldown' in form_data:
            valid, error = self.validate_integer_range(
                form_data['post_playback_cooldown'], 0, 60, 'Post-playback cooldown'
            )
            if valid:
                sanitized['post_playback_cooldown_minutes'] = int(form_data['post_playback_cooldown'])
            else:
                errors.append(error)
        
        # Validate volume
        if 'volume' in form_data:
            valid, error = self.validate_integer_range(
                form_data['volume'], 0, 100, 'Volume'
            )
            if valid:
                sanitized['volume'] = int(form_data['volume'])
            else:
                errors.append(error)
        
        # Validate night mode times (HH:MM format)
        if 'night_start' in form_data:
            if self.validate_time_format(form_data['night_start']):
                sanitized['night_mode_start'] = form_data['night_start']
            else:
                errors.append("Night mode start time must be in HH:MM format")
        
        if 'night_end' in form_data:
            if self.validate_time_format(form_data['night_end']):
                sanitized['night_mode_end'] = form_data['night_end']
            else:
                errors.append("Night mode end time must be in HH:MM format")
        
        # Validate button disable times (optional, HH:MM format)
        if 'button_disable_start' in form_data and form_data['button_disable_start']:
            if self.validate_time_format(form_data['button_disable_start']):
                sanitized['button_disable_start'] = form_data['button_disable_start']
            else:
                errors.append("Button disable start time must be in HH:MM format")
        else:
            sanitized['button_disable_start'] = None
        
        if 'button_disable_end' in form_data and form_data['button_disable_end']:
            if self.validate_time_format(form_data['button_disable_end']):
                sanitized['button_disable_end'] = form_data['button_disable_end']
            else:
                errors.append("Button disable end time must be in HH:MM format")
        else:
            sanitized['button_disable_end'] = None
        
        # Validate boolean settings
        sanitized['button_enabled'] = 'button_enabled' in form_data
        sanitized['second_press_stops'] = 'second_press_stops' in form_data
        sanitized['motion_sensor_enabled'] = 'motion_sensor_enabled' in form_data
        sanitized['motion_stop_enabled'] = 'motion_stop_enabled' in form_data
        
        # Validate motion stop timeout
        if 'motion_stop_timeout' in form_data:
            try:
                timeout = int(form_data['motion_stop_timeout'])
                if timeout < 0:
                    errors.append("Motion stop timeout must be non-negative")
                else:
                    sanitized['motion_stop_timeout_seconds'] = timeout
            except (ValueError, TypeError):
                errors.append("Motion stop timeout must be a valid number")
        
        # GPIO pins are configured in config file only, not via web interface
        
        # Validate schedule
        if 'play_schedule' in form_data:
            valid, schedule_or_errors = self.validate_schedule_list(form_data['play_schedule'])
            if valid:
                sanitized['play_schedule'] = schedule_or_errors
            else:
                errors.extend(schedule_or_errors)
        
        return len(errors) == 0, sanitized, errors


class CSRFProtection:
    """Simple CSRF protection for form submissions."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.logger = logging.getLogger(__name__)
    
    def generate_token(self) -> str:
        """Generate CSRF token."""
        import hashlib
        import time
        
        timestamp = str(int(time.time()))
        token_data = f"{self.secret_key}:{timestamp}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        
        return f"{timestamp}:{token}"
    
    def validate_token(self, token: str, max_age: int = 3600) -> bool:
        """Validate CSRF token.
        
        Args:
            token: Token to validate
            max_age: Maximum age in seconds
            
        Returns:
            True if valid, False otherwise
        """
        if not token:
            return False
        
        try:
            import hashlib
            import time
            
            parts = token.split(':')
            if len(parts) != 2:
                return False
            
            timestamp_str, token_hash = parts
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            
            # Check if token is not expired
            if current_time - timestamp > max_age:
                self.logger.warning("CSRF token expired")
                return False
            
            # Verify token
            expected_data = f"{self.secret_key}:{timestamp_str}"
            expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
            
            return token_hash == expected_hash
            
        except (ValueError, TypeError) as e:
            self.logger.warning("Invalid CSRF token format: %s", e)
            return False


def setup_security_headers(app):
    """Add security headers to Flask app."""
    
    @app.after_request
    def add_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
