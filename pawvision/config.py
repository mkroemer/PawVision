"""Configuration management for PawVision."""

import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class PawVisionConfig:
    """PawVision configuration with validation."""
    
    # Video settings
    playback_duration_minutes: int = 30  # Renamed from timeout_minutes
    post_playback_cooldown_minutes: int = 5  # New: cooldown after video ends
    volume: int = 50
    
    # Night mode settings (HH:MM string format only)
    night_mode_start: str = "22:00"
    night_mode_end: str = "06:00"
    
    # Button settings (HH:MM string format only)
    button_enabled: bool = True
    button_disable_start: Optional[str] = None
    button_disable_end: Optional[str] = None
    second_press_stops: bool = True
    button_cooldown_seconds: int = 60
    
    # Hardware settings
    monitor_gpio: Optional[int] = None
    button_pin: int = 17
    motion_sensor_pin: Optional[int] = None  # New: motion sensor GPIO pin
    motion_sensor_enabled: bool = False  # New: enable/disable motion sensor
    motion_stop_enabled: bool = False  # New: stop video when no motion detected
    motion_stop_timeout_seconds: int = 300  # New: seconds to wait before stopping (5 minutes)
    
    # Schedule settings
    play_schedule: Optional[List[str]] = None
    
    # Statistics settings
    enable_statistics: bool = True
    statistics_file: Optional[str] = None
    statistics_db: Optional[str] = None
    
    # Performance settings
    enable_duration_cache: bool = True
    cache_file: Optional[str] = None
    database_path: Optional[str] = None  # Unified database path for video library and statistics
    
    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if self.play_schedule is None:
            self.play_schedule = []
        self.validate()
    
    def validate(self):
        """Validate configuration values."""
        errors = []
        
        # Volume validation
        if not 0 <= self.volume <= 100:
            errors.append("Volume must be between 0 and 100")
        
        # Playback duration validation
        if self.playback_duration_minutes <= 0:
            errors.append("Playback duration must be positive")
        
        # Post-playback cooldown validation
        if self.post_playback_cooldown_minutes < 0:
            errors.append("Post-playback cooldown must be non-negative")
        
        # Night mode validation (HH:MM format only)
        if not self._validate_time_format(self.night_mode_start):
            errors.append("Night mode start must be in valid HH:MM format")
        if not self._validate_time_format(self.night_mode_end):
            errors.append("Night mode end must be in valid HH:MM format")
        
        # Button disable times validation (HH:MM format only)
        if self.button_disable_start is not None:
            if not self._validate_time_format(self.button_disable_start):
                errors.append("Button disable start must be in valid HH:MM format")
        
        if self.button_disable_end is not None:
            if not self._validate_time_format(self.button_disable_end):
                errors.append("Button disable end must be in valid HH:MM format")
        
        # GPIO pin validation
        if self.monitor_gpio is not None:
            if not 1 <= self.monitor_gpio <= 40:
                errors.append("Monitor GPIO must be between 1 and 40")
        
        if not 1 <= self.button_pin <= 40:
            errors.append("Button pin must be between 1 and 40")
        
        if self.motion_sensor_pin is not None:
            if not 1 <= self.motion_sensor_pin <= 40:
                errors.append("Motion sensor pin must be between 1 and 40")
            # Check for pin conflicts
            if self.motion_sensor_pin == self.button_pin:
                errors.append("Motion sensor pin cannot be the same as button pin")
            if self.motion_sensor_pin == self.monitor_gpio:
                errors.append("Motion sensor pin cannot be the same as monitor GPIO")
        
        # Motion stop validation
        if self.motion_stop_timeout_seconds < 0:
            errors.append("Motion stop timeout must be non-negative")
        
        # Schedule validation
        for time_str in self.play_schedule:
            if not self._validate_time_format(time_str):
                errors.append(f"Invalid time format: {time_str}")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _validate_time_format(self, time_str: str) -> bool:
        """Validate HH:MM time format."""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, AttributeError):
            return False
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return asdict(self)


class ConfigManager:
    """Manages configuration loading, saving, and updates."""
    
    def __init__(self, config_file: str, dev_mode: bool = False):
        self.config_file = config_file
        self.dev_mode = dev_mode
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> PawVisionConfig:
        """Load and validate configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Backward compatibility: handle old field names
                if 'timeout_minutes' in data and 'playback_duration_minutes' not in data:
                    data['playback_duration_minutes'] = data.pop('timeout_minutes')
                
                # Set dev mode specific defaults
                if self.dev_mode:
                    data.setdefault('statistics_file', './pawvision_stats.json')
                    data.setdefault('statistics_db', './pawvision_stats.db')
                    data.setdefault('cache_file', './pawvision_cache.json')
                    data.setdefault('database_path', './pawvision.db')
                else:
                    data.setdefault('statistics_file', '/home/pi/pawvision_stats.json')
                    data.setdefault('statistics_db', '/home/pi/pawvision_stats.db')
                    data.setdefault('cache_file', '/home/pi/pawvision_cache.json')
                    data.setdefault('database_path', '/home/pi/pawvision.db')
                
                config = PawVisionConfig(**data)
                self.logger.info("Configuration loaded from %s", self.config_file)
                return config
            else:
                self.logger.info("Configuration file not found, creating default: %s", self.config_file)
                config = PawVisionConfig()
                
                # Set dev mode specific defaults
                if self.dev_mode:
                    config.statistics_file = './pawvision_stats.json'
                    config.statistics_db = './pawvision_stats.db'
                    config.cache_file = './pawvision_cache.json'
                    config.database_path = './pawvision.db'
                else:
                    config.statistics_file = '/home/pi/pawvision_stats.json'
                    config.statistics_db = '/home/pi/pawvision_stats.db'
                    config.cache_file = '/home/pi/pawvision_cache.json'
                    config.database_path = '/home/pi/pawvision.db'
                
                self.save_config(config)
                return config
        
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error("Error loading configuration: %s", e)
            self.logger.info("Creating backup of invalid config and using defaults")
            
            # Backup invalid config
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                os.rename(self.config_file, backup_file)
                self.logger.info("Invalid config backed up to %s", backup_file)
            
            # Create default config
            config = PawVisionConfig()
            if self.dev_mode:
                config.statistics_file = './pawvision_stats.json'
                config.statistics_db = './pawvision_stats.db'
                config.cache_file = './pawvision_cache.json'
                config.database_path = './pawvision.db'
            else:
                config.statistics_file = '/home/pi/pawvision_stats.json'
                config.statistics_db = '/home/pi/pawvision_stats.db'
                config.cache_file = '/home/pi/pawvision_cache.json'
                config.database_path = '/home/pi/pawvision.db'
                config.cache_file = '/home/pi/pawvision_cache.json'
            
            self.save_config(config)
            return config
    
    def save_config(self, config: PawVisionConfig):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            self.logger.info("Configuration saved to %s", self.config_file)
        
        except Exception as e:
            self.logger.error("Error saving configuration: %s", e)
            raise
    
    def update_config(self, config: PawVisionConfig, updates: dict) -> PawVisionConfig:
        """Update configuration with new values."""
        config_dict = config.to_dict()
        config_dict.update(updates)
        
        new_config = PawVisionConfig(**config_dict)
        self.save_config(new_config)
        
        self.logger.info("Configuration updated: %s", list(updates.keys()))
        return new_config


def get_video_directories(dev_mode: bool) -> List[str]:
    """Get video directories based on mode."""
    if dev_mode:
        return ["./videos"]
    else:
        return ["/home/pi/videos", "/media/usb"]


def get_default_port(dev_mode: bool) -> int:
    """Get default port based on mode."""
    return 5001 if dev_mode else 5000
