"""Main PawVision application."""

import os
import sys
import signal
import atexit
import logging
import threading
from pathlib import Path

# Add the pawvision package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pawvision.config import ConfigManager, get_video_directories, get_default_port
from pawvision.logging_config import setup_logging, log_system_info
from pawvision.statistics_unified import StatisticsManager
from pawvision.video_player import VideoPlayer
from pawvision.gpio_handler import GPIOManager
from pawvision.web_interface import WebInterface


class PawVisionApp:
    """Main PawVision application class."""
    
    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode
        self.logger = None
        self.config = None
        self.config_manager = None
        self.statistics_manager = None
        self.video_player = None
        self.gpio_manager = None
        self.web_interface = None
        self.web_thread = None
        self.running = False
        
        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, _frame):
        """Handle shutdown signals."""
        if self.logger:
            self.logger.info("Received signal %d, shutting down...", signum)
        self.stop()
    
    def initialize(self):
        """Initialize all components."""
        try:
            # Determine configuration file path
            if self.dev_mode:
                config_file = "./pawvision_settings.json"
                log_file = "./pawvision.log"
            else:
                config_file = "/home/pi/pawvision_settings.json"
                log_file = "/home/pi/pawvision.log"
            
            # Initialize logging
            setup_logging(
                log_level=logging.DEBUG if self.dev_mode else logging.INFO,
                log_file=log_file,
                dev_mode=self.dev_mode
            )
            self.logger = logging.getLogger(__name__)
            
            self.logger.info("=== PawVision Starting ===")
            self.logger.info("Version: 2.0.0")
            self.logger.info("Dev mode: %s", self.dev_mode)
            
            # Log system information
            log_system_info()
            
            # Initialize configuration
            self.config_manager = ConfigManager(config_file, self.dev_mode)
            self.config = self.config_manager.load_config()
            
            # Add dev_mode to config for components
            self.config.dev_mode = self.dev_mode
            
            self.logger.info("Configuration loaded successfully")
            
            # Initialize statistics
            if self.config.enable_statistics:
                self.statistics_manager = StatisticsManager(
                    self.config.database_path,
                    self.config.statistics_file,  # For migration purposes
                    self.config.enable_statistics,
                    self.config.button_cooldown_seconds
                )
                self.logger.info("Statistics manager initialized")
            else:
                self.logger.info("Statistics disabled")
            
            # Get video directories
            video_dirs = get_video_directories(self.dev_mode)
            self.logger.info("Video directories: %s", video_dirs)
            
            # Initialize video player
            self.video_player = VideoPlayer(
                self.config,
                video_dirs,
                self.statistics_manager
            )
            self.logger.info("Video player initialized")
            
            # Add default YouTube video if none exist
            self._add_default_video()
            
            # Initialize GPIO manager
            self.gpio_manager = GPIOManager(
                self.config,
                self.video_player,
                self.statistics_manager
            )
            self.logger.info("GPIO manager initialized")
            
            # Initialize web interface
            self.web_interface = WebInterface(
                self.config,
                self.video_player,
                self.statistics_manager,
                self.gpio_manager,
                self.config_manager
            )
            self.logger.info("Web interface initialized")
            
            self.logger.info("All components initialized successfully")
            return True
            
        except (OSError, ValueError, ImportError) as e:
            if self.logger:
                self.logger.error("Failed to initialize PawVision: %s", e)
            else:
                print(f"Failed to initialize PawVision: {e}")
            return False
    
    def start(self):
        """Start the application."""
        try:
            self.logger.info("Starting PawVision application")
            
            # Start GPIO manager (includes scheduler)
            self.gpio_manager.start()
            
            # Start web interface in a separate thread
            port = get_default_port(self.dev_mode)
            
            self.web_thread = threading.Thread(
                target=self.web_interface.run,
                kwargs={
                    'host': "0.0.0.0",
                    'port': port,
                    'debug': False  # Never use debug mode in threaded environment
                },
                daemon=True,
                name="PawVision-Web"
            )
            self.web_thread.start()
            
            self.running = True
            self.logger.info("PawVision started successfully")
            self.logger.info("Web interface available at http://localhost:%d", port)
            
            # Print startup message
            print("🐾 PawVision v2.0.0 started successfully!")
            print(f"📺 Web interface: http://localhost:{port}")
            print(f"📊 Statistics: {'Enabled' if self.statistics_manager else 'Disabled'}")
            print(f"🎮 Dev mode: {'Yes' if self.dev_mode else 'No'}")
            print(f"📁 Videos found: {len(self.video_player.get_all_videos())}")
            
            if self.dev_mode:
                print("🔧 Dev endpoints:")
                print(f"   - Button simulation: http://localhost:{port}/dev/button")
                print(f"   - Clear cache: http://localhost:{port}/dev/cache/clear")
            
            return True
            
        except (OSError, ValueError) as e:
            self.logger.error("Failed to start PawVision: %s", e)
            return False
    
    def stop(self):
        """Stop the application."""
        if not self.running:
            return
        
        self.running = False
        
        if self.logger:
            self.logger.info("Stopping PawVision application")
        
        # Stop components in reverse order
        if self.gpio_manager:
            self.gpio_manager.stop()
        
        if self.video_player:
            self.video_player.stop_video()
        
        if self.logger:
            self.logger.info("PawVision stopped")
    
    def cleanup(self):
        """Clean up all resources."""
        if self.logger:
            self.logger.info("Cleaning up PawVision resources")
        
        # Cleanup components
        if self.gpio_manager:
            self.gpio_manager.cleanup()
        
        if self.video_player:
            self.video_player.cleanup()
        
        # SQLite statistics manager doesn't need explicit cleanup
        # Database connections are automatically closed
        
        if self.logger:
            self.logger.info("PawVision cleanup complete")
    
    def _add_default_video(self):
        """Add a default YouTube video if no videos exist in the library."""
        try:
            # Check if there are any videos in the library (both local files and database entries)
            existing_videos = self.video_player.get_video_library_entries()
            if existing_videos:
                self.logger.debug("Videos already exist in library, skipping default video")
                return
            
            # Add the default YouTube video
            youtube_manager = self.video_player.library_manager.youtube_manager
            if youtube_manager:
                self.logger.info("Adding default YouTube video: MrSYP-cotdg")
                
                video_entry = youtube_manager.create_video_entry(
                    url="https://www.youtube.com/watch?v=MrSYP-cotdg",
                    custom_title="Unlimited Birds Chipmunks Squirrels",
                    custom_start_time=8.0,
                    custom_end_offset=None,
                    quality="720p",
                    download=False
                )
                
                if video_entry:
                    # Add to database
                    success = self.video_player.library_manager.add_or_update_video(video_entry)
                    if success:
                        self.logger.info("Default YouTube video added successfully")
                    else:
                        self.logger.error("Failed to add default video to database")
                else:
                    self.logger.error("Failed to create default video entry")
            else:
                self.logger.warning("YouTube manager not available, cannot add default video")
                
        except Exception as e:
            self.logger.error("Error adding default video: %s", e)
    
    def run_forever(self):
        """Run the application until interrupted."""
        try:
            # Keep main thread alive
            while self.running:
                import time
                time.sleep(1)
                
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Keyboard interrupt received")
            self.stop()


def detect_dev_mode():
    """Detect if we should run in development mode."""
    # Check for explicit environment variable
    dev_env = os.environ.get('PAWVISION_DEV_MODE', '').lower()
    if dev_env in ('1', 'true', 'yes'):
        return True
    
    # Auto-detect based on system
    if os.path.exists('/home/pi'):
        return False  # Likely on Raspberry Pi
    
    # Check if gpiozero is available
    try:
        import gpiozero  # noqa: F401
        return False  # GPIO library available, likely Pi
    except ImportError:
        return True  # No GPIO library, likely dev environment


def main():
    """Main entry point."""
    # Detect mode
    dev_mode = detect_dev_mode()
    
    print("🐾 PawVision v2.0.0")
    print(f"🔧 Mode: {'Development' if dev_mode else 'Production'}")
    
    # Create and initialize application
    app = PawVisionApp(dev_mode=dev_mode)
    
    if not app.initialize():
        print("❌ Failed to initialize PawVision")
        sys.exit(1)
    
    if not app.start():
        print("❌ Failed to start PawVision")
        sys.exit(1)
    
    try:
        app.run_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        app.cleanup()
        # Only shutdown logging if not running under pytest
        import os, logging
        if 'PYTEST_CURRENT_TEST' not in os.environ:
            logging.shutdown()


if __name__ == "__main__":
    main()
