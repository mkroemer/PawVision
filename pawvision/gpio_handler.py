"""GPIO and button handling for PawVision."""

import logging
import threading
import time
from datetime import datetime
from typing import Optional
from .time_utils import time_parser


class ButtonHandler:
    """Handles physical button presses, scheduling, and motion sensor."""
    
    def __init__(self, config, video_player, statistics_manager=None):
        self.config = config
        self.video_player = video_player
        self.statistics_manager = statistics_manager
        self.button = None
        self.motion_sensor = None
        self.logger = logging.getLogger(__name__)
        self._last_press_time = 0
        self._debounce_time = 0.5  # 500ms debounce
        
        self._init_button()
        self._init_motion_sensor()
    
    def _init_button(self):
        """Initialize GPIO button if not in dev mode."""
        dev_mode = getattr(self.config, 'dev_mode', False)
        
        if dev_mode:
            self.logger.info("DEV_MODE: GPIO button disabled")
            return
        
        try:
            from gpiozero import Button
            self.button = Button(self.config.button_pin, pull_up=True)
            self.button.when_pressed = self._handle_button_press
            self.logger.info("Button initialized on GPIO pin %d", self.config.button_pin)
            
        except ImportError:
            self.logger.warning("gpiozero not available, button control disabled")
        except (OSError, ValueError) as e:
            self.logger.error("Error initializing button: %s", e)
    
    def _init_motion_sensor(self):
        """Initialize motion sensor if enabled and not in dev mode."""
        dev_mode = getattr(self.config, 'dev_mode', False)
        
        if dev_mode:
            self.logger.info("DEV_MODE: Motion sensor disabled")
            return
        
        if not self.config.motion_sensor_enabled or self.config.motion_sensor_pin is None:
            self.logger.info("Motion sensor disabled in configuration")
            return
        
        try:
            from gpiozero import MotionSensor
            self.motion_sensor = MotionSensor(self.config.motion_sensor_pin)
            self.motion_sensor.when_no_motion = self._handle_motion_lost
            self.logger.info("Motion sensor initialized on GPIO pin %d", self.config.motion_sensor_pin)
            
        except ImportError:
            self.logger.warning("gpiozero not available, motion sensor disabled")
        except (OSError, ValueError) as e:
            self.logger.error("Error initializing motion sensor: %s", e)
    
    def _handle_motion_lost(self):
        """Handle when motion is no longer detected (pet stopped watching)."""
        if self.video_player.is_playing():
            self.logger.info("Motion lost - stopping video playback")
            self.video_player.stop_video("motion_sensor")

    def _handle_button_press(self):
        """Handle physical button press."""
        if not self.is_button_allowed():
            self.logger.info("Button press ignored - disabled by schedule")
            return
        
        # Determine action based on current state
        if self.video_player.is_playing():
            if self.config.second_press_stops:
                self.logger.info("Button pressed - stopping video")
                
                # Record button press as interruption (with cooldown protection)
                button_allowed = True
                if self.statistics_manager:
                    current_video = getattr(self.video_player, 'current_video', None)
                    button_allowed = self.statistics_manager.record_button_press(
                        self.config.button_cooldown_seconds, 
                        video_path=current_video,
                        is_interruption=True
                    )
                
                if button_allowed:
                    success = self.video_player.stop_video()
                    if not success:
                        self.logger.warning("Failed to stop video")
                else:
                    self.logger.info("Button press blocked by cooldown period")
            else:
                self.logger.info("Button pressed while playing - ignoring (second_press_stops disabled)")
        else:
            self.logger.info("Button pressed - starting video")
            
            # Record button press (with cooldown protection)
            button_allowed = True
            if self.statistics_manager:
                button_allowed = self.statistics_manager.record_button_press(
                    self.config.button_cooldown_seconds,
                    is_interruption=False
                )
            
            if button_allowed:
                success = self.video_player.play_random_video("button")
                if not success:
                    self.logger.warning("Failed to start video")
            else:
                self.logger.info("Button press blocked by cooldown period")
    
    def is_button_allowed(self) -> bool:
        """Check if button is allowed based on settings and schedule."""
        if not self.config.button_enabled:
            return False
        
        # Use centralized time parsing utility
        in_disable_range = time_parser.is_time_in_range(
            self.config.button_disable_start,
            self.config.button_disable_end
        )
        
        # Return True if NOT in disable range
        return not in_disable_range
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if self.button:
            try:
                self.button.close()
                self.logger.info("Button GPIO cleaned up")
            except (AttributeError, OSError) as e:
                self.logger.error("Error cleaning up button GPIO: %s", e)
        
        if self.motion_sensor:
            try:
                self.motion_sensor.close()
                self.logger.info("Motion sensor GPIO cleaned up")
            except (AttributeError, OSError) as e:
                self.logger.error("Error cleaning up motion sensor GPIO: %s", e)


class Scheduler:
    """Handles scheduled video playback."""
    
    def __init__(self, config, video_player, statistics_manager=None):
        self.config = config
        self.video_player = video_player
        self.statistics_manager = statistics_manager
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.scheduler_thread = None
        self._last_checked = None
    
    def start(self):
        """Start the scheduler loop."""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="PawVision-Scheduler"
        )
        self.scheduler_thread.start()
        self.logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler loop."""
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                self._check_schedule()
                time.sleep(10)  # Check every 10 seconds
            except (OSError, KeyboardInterrupt) as e:
                self.logger.error("Error in scheduler loop: %s", e)
                time.sleep(30)  # Wait longer after error
    
    def _check_schedule(self):
        """Check if any scheduled plays should trigger."""
        if not self.config.play_schedule:
            return
        
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # Only check once per minute
        if current_time_str == self._last_checked:
            return
        
        self._last_checked = current_time_str
        
        if current_time_str in self.config.play_schedule:
            self.logger.info("Scheduled play triggered at %s", current_time_str)
            
            # Don't start if already playing
            if self.video_player.is_playing():
                self.logger.info("Video already playing, skipping scheduled play")
                return
            
            success = self.video_player.play_random_video("scheduled")
            
            if self.statistics_manager:
                self.statistics_manager.record_scheduled_play(current_time_str)
            
            if success:
                self.logger.info("Scheduled video started successfully")
            else:
                self.logger.warning("Failed to start scheduled video")
    
    def get_next_scheduled_play(self) -> Optional[str]:
        """Get the next scheduled play time."""
        if not self.config.play_schedule:
            return None
        
        now = datetime.now()
        current_time = now.hour * 60 + now.minute
        
        # Convert schedule times to minutes
        schedule_minutes = []
        for time_str in self.config.play_schedule:
            try:
                hour, minute = map(int, time_str.split(':'))
                schedule_minutes.append(hour * 60 + minute)
            except ValueError:
                continue
        
        if not schedule_minutes:
            return None
        
        # Find next time
        schedule_minutes.sort()
        
        for scheduled_time in schedule_minutes:
            if scheduled_time > current_time:
                hour = scheduled_time // 60
                minute = scheduled_time % 60
                return f"{hour:02d}:{minute:02d}"
        
        # If no time today, return first time tomorrow
        first_time = schedule_minutes[0]
        hour = first_time // 60
        minute = first_time % 60
        return f"{hour:02d}:{minute:02d} (tomorrow)"
    
    def cleanup(self):
        """Clean up scheduler resources."""
        self.stop()


class GPIOManager:
    """Manages all GPIO-related functionality."""
    
    def __init__(self, config, video_player, statistics_manager=None):
        self.config = config
        self.video_player = video_player
        self.statistics_manager = statistics_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.button_handler = ButtonHandler(
            config, video_player, statistics_manager
        )
        self.scheduler = Scheduler(
            config, video_player, statistics_manager
        )
    
    def start(self):
        """Start all GPIO components."""
        self.logger.info("Starting GPIO manager")
        self.scheduler.start()
    
    def stop(self):
        """Stop all GPIO components."""
        self.logger.info("Stopping GPIO manager")
        self.scheduler.stop()
    
    def cleanup(self):
        """Clean up all GPIO resources."""
        self.logger.info("Cleaning up GPIO manager")
        self.button_handler.cleanup()
        self.scheduler.cleanup()
    
    def is_button_allowed(self) -> bool:
        """Check if button is currently allowed."""
        return self.button_handler.is_button_allowed()
    
    def get_next_scheduled_play(self) -> Optional[str]:
        """Get next scheduled play time."""
        return self.scheduler.get_next_scheduled_play()
    
    def simulate_button_press(self):
        """Simulate button press (for development/testing)."""
        self.logger.info("Manual button press triggered")
        self.button_handler._handle_button_press()
