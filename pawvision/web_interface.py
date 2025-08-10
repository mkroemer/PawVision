"""Web interface for PawVision."""

import logging
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from .security import SecurityValidator, setup_security_headers


class WebInterface:
    """Manages the Flask web interface."""
    
    def __init__(self, config, video_player, statistics_manager, gpio_manager, config_manager):
        self.config = config
        self.video_player = video_player
        self.statistics_manager = statistics_manager
        self.gpio_manager = gpio_manager
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        
        # Configure Flask
        self.app.config['SECRET_KEY'] = 'pawvision-secret-key-change-in-production'
        self.app.config['MAX_CONTENT_LENGTH'] = SecurityValidator.MAX_FILE_SIZE
        
        # Initialize security
        self.validator = SecurityValidator()
        setup_security_headers(self.app)
        
        # Register routes
        self._register_routes()
        
        # Register error handlers
        self._register_error_handlers()
    
    def _register_routes(self):
        """Register all Flask routes."""
        
        @self.app.route("/")
        def index():
            """Main dashboard page."""
            try:
                videos = self.video_player.get_video_info()
                stats_summary = None
                
                if self.statistics_manager:
                    stats_summary = self.statistics_manager.get_summary()
                
                next_play = self.gpio_manager.get_next_scheduled_play()
                
                return render_template("index.html", 
                                     videos=videos,
                                     settings=self.config.to_dict(),
                                     is_playing=self.video_player.is_playing(),
                                     stats=stats_summary,
                                     next_scheduled_play=next_play)
            
            except (OSError, ValueError) as e:
                self.logger.error("Error rendering index page: %s", e)
                return "Internal server error", 500
        
        @self.app.route("/upload", methods=["POST"])
        def upload_video():
            """Handle video file upload."""
            try:
                if 'file' not in request.files:
                    return jsonify({"error": "No file selected"}), 400
                
                file = request.files['file']
                
                # Validate file
                valid, result = self.validator.validate_video_file(file)
                if not valid:
                    return jsonify({"error": result}), 400
                
                filename = result
                
                # Get upload directory
                video_dirs = [d for d in self.video_player.video_dirs if os.path.exists(d)]
                if not video_dirs:
                    return jsonify({"error": "No video directory available"}), 500
                
                upload_dir = video_dirs[0]
                save_path = os.path.join(upload_dir, filename)
                
                # Check if file already exists
                if os.path.exists(save_path):
                    return jsonify({"error": f"File {filename} already exists"}), 409
                
                # Save file
                file.save(save_path)
                
                self.logger.info("Video uploaded: %s", filename)
                return jsonify({"success": f"Uploaded {filename}"}), 200
            
            except RequestEntityTooLarge:
                return jsonify({"error": "File too large"}), 413
            except OSError as e:
                self.logger.error("Upload error: %s", e)
                return jsonify({"error": "Upload failed"}), 500
        
        @self.app.route("/delete", methods=["POST"])
        def delete_video():
            """Handle video file deletion."""
            try:
                video_path = request.form.get("path")
                if not video_path:
                    return jsonify({"error": "No file path provided"}), 400
                
                # Validate path
                if not self.validator.validate_file_path(video_path, self.video_player.video_dirs):
                    return jsonify({"error": "Invalid file path"}), 400
                
                if not os.path.exists(video_path):
                    return jsonify({"error": "File not found"}), 404
                
                # Delete file
                os.remove(video_path)
                
                filename = os.path.basename(video_path)
                self.logger.info("Video deleted: %s", filename)
                
                return jsonify({"success": f"Deleted {filename}"}), 200
            
            except OSError as e:
                self.logger.error("Delete error: %s", e)
                return jsonify({"error": "Delete failed"}), 500
        
        @self.app.route("/settings", methods=["POST"])
        def update_settings():
            """Handle settings update."""
            try:
                # Validate and sanitize form data
                valid, sanitized_data, errors = self.validator.sanitize_settings_update(request.form)
                
                if not valid:
                    error_msg = "; ".join(errors)
                    return jsonify({"error": error_msg}), 400
                
                # Update configuration
                self.config = self.config_manager.update_config(self.config, sanitized_data)
                
                self.logger.info("Settings updated successfully")
                # Redirect back to the main page instead of returning JSON
                return redirect(url_for('index'))
            
            except ValueError as e:
                self.logger.error("Settings validation error: %s", e)
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                self.logger.error("Settings update error: %s", e)
                return jsonify({"error": "Settings update failed"}), 500
        
        @self.app.route("/video/update", methods=["POST"])
        def update_video():
            """Handle video metadata update."""
            try:
                video_path = request.form.get("path")
                title = request.form.get("title", "").strip()
                custom_start_time = request.form.get("custom_start_time")
                custom_end_time = request.form.get("custom_end_time")
                
                if not video_path:
                    return jsonify({"error": "No file path provided"}), 400
                
                # Validate path
                if not self.validator.validate_file_path(video_path, self.video_player.video_dirs):
                    return jsonify({"error": "Invalid file path"}), 400
                
                if not os.path.exists(video_path):
                    return jsonify({"error": "File not found"}), 404
                
                # Parse and validate times
                start_time = None
                end_time = None
                
                if custom_start_time:
                    try:
                        start_time = float(custom_start_time)
                        if start_time < 0:
                            return jsonify({"error": "Start time cannot be negative"}), 400
                    except ValueError:
                        return jsonify({"error": "Invalid start time format"}), 400
                
                if custom_end_time:
                    try:
                        end_time = float(custom_end_time)
                        if end_time <= 0:
                            return jsonify({"error": "End time must be positive"}), 400
                        if start_time is not None and end_time <= start_time:
                            return jsonify({"error": "End time must be after start time"}), 400
                    except ValueError:
                        return jsonify({"error": "Invalid end time format"}), 400
                
                # Update video metadata
                success = self.video_player.update_video_metadata(
                    video_path, 
                    title if title else None, 
                    start_time, 
                    end_time
                )
                
                if success:
                    filename = os.path.basename(video_path)
                    self.logger.info("Video metadata updated: %s", filename)
                    return redirect(url_for('index'))
                else:
                    return jsonify({"error": "Failed to update video metadata"}), 500
                
            except Exception as e:
                self.logger.error("Video update error: %s", e)
                return jsonify({"error": "Update failed"}), 500
        
        # API Routes
        @self.app.route("/api/play", methods=["POST"])
        def api_play():
            """API endpoint to start video playback."""
            try:
                if self.video_player.is_playing():
                    return jsonify({"error": "Video already playing"}), 409
                
                success = self.video_player.play_random_video("api")
                
                if self.statistics_manager:
                    self.statistics_manager.record_api_call("play")
                
                if success:
                    return jsonify({"status": "playing"}), 200
                else:
                    return jsonify({"error": "Failed to start playback"}), 500
            
            except Exception as e:
                self.logger.error("API play error: %s", e)
                return jsonify({"error": "Internal error"}), 500
        
        @self.app.route("/api/stop", methods=["POST"])
        def api_stop():
            """API endpoint to stop video playback."""
            try:
                success = self.video_player.stop_video()
                
                if self.statistics_manager:
                    self.statistics_manager.record_api_call("stop")
                
                if success:
                    return jsonify({"status": "stopped"}), 200
                else:
                    return jsonify({"status": "not_playing"}), 200
            
            except Exception as e:
                self.logger.error("API stop error: %s", e)
                return jsonify({"error": "Internal error"}), 500
        
        @self.app.route("/api/status")
        def api_status():
            """API endpoint to get current status."""
            try:
                status = {
                    "is_playing": self.video_player.is_playing(),
                    "button_allowed": self.gpio_manager.is_button_allowed(),
                    "next_scheduled_play": self.gpio_manager.get_next_scheduled_play(),
                    "night_mode": self.video_player.is_night_mode(),
                    "video_count": len(self.video_player.get_all_videos())
                }
                
                return jsonify(status), 200
            
            except Exception as e:
                self.logger.error("API status error: %s", e)
                return jsonify({"error": "Internal error"}), 500
        
        @self.app.route("/api/health")
        def api_health():
            """Health check endpoint for monitoring."""
            try:
                health_data = {
                    "status": "healthy",
                    "version": "2.0.0",
                    "timestamp": self._get_timestamp(),
                    "is_playing": self.video_player.is_playing(),
                    "video_count": len(self.video_player.get_all_videos())
                }
                
                if self.statistics_manager:
                    stats = self.statistics_manager.get_summary()
                    health_data["stats"] = {
                        "total_button_presses": stats["total_button_presses"],
                        "total_video_plays": stats["total_video_plays"],
                        "total_api_calls": stats["total_api_calls"]
                    }
                
                return jsonify(health_data), 200
            
            except Exception as e:
                self.logger.error("Health check error: %s", e)
                return jsonify({"status": "unhealthy", "error": str(e)}), 500
        
        @self.app.route("/api/statistics")
        def api_statistics():
            """API endpoint to get detailed statistics."""
            try:
                if not self.statistics_manager:
                    return jsonify({"status": "error", "message": "Statistics not enabled"}), 404
                
                stats = self.statistics_manager.get_summary()
                
                # Transform data for frontend
                frontend_stats = {
                    "status": "success",
                    "statistics": {
                        "total_button_presses": stats.get("total_button_presses", 0),
                        "today_button_presses": stats.get("today_button_presses", 0),
                        "daily_average": stats.get("daily_average", 0),
                        "peak_hour": stats.get("peak_hour", "N/A"),
                        "total_viewing_minutes": stats.get("total_viewing_minutes", 0),
                        "yesterday_viewing_minutes": stats.get("yesterday_viewing_minutes", 0)
                    }
                }
                
                return jsonify(frontend_stats), 200
            
            except Exception as e:
                self.logger.error("API statistics error: %s", e)
                return jsonify({"status": "error", "message": "Internal error"}), 500
        
        @self.app.route("/api/statistics/hourly")
        def api_hourly_statistics():
            """API endpoint to get hourly statistics for a specific date."""
            try:
                if not self.statistics_manager:
                    return jsonify({"status": "error", "message": "Statistics not enabled"}), 404
                
                date_str = request.args.get('date')  # Expected format: YYYY-MM-DD
                hourly_data = self.statistics_manager.get_hourly_data(date_str)
                
                return jsonify({
                    "status": "success",
                    "date": date_str or "today",
                    "hourly_data": hourly_data
                }), 200
            
            except Exception as e:
                self.logger.error("API hourly statistics error: %s", e)
                return jsonify({"status": "error", "message": "Internal error"}), 500
        
        @self.app.route("/api/statistics/clear", methods=["POST"])
        def api_clear_statistics():
            """API endpoint to clear all statistics."""
            try:
                if not self.statistics_manager:
                    return jsonify({"status": "error", "message": "Statistics not enabled"}), 404
                
                self.statistics_manager.reset_stats()
                self.logger.info("Statistics cleared via web interface")
                
                return jsonify({"status": "success", "message": "Statistics cleared"}), 200
            
            except Exception as e:
                self.logger.error("API clear statistics error: %s", e)
                return jsonify({"status": "error", "message": "Internal error"}), 500
        
        # Development routes
        if getattr(self.config, 'dev_mode', False):
            @self.app.route("/dev/button")
            def dev_button():
                """Simulate button press for development."""
                try:
                    self.gpio_manager.simulate_button_press()
                    return jsonify({"success": "Button press simulated"}), 200
                except Exception as e:
                    self.logger.error("Dev button error: %s", e)
                    return jsonify({"error": str(e)}), 500
            
            @self.app.route("/dev/cache/clear")
            def dev_clear_cache():
                """Clear video duration cache for development."""
                try:
                    self.video_player.cleanup_cache()
                    return jsonify({"success": "Cache cleared"}), 200
                except Exception as e:
                    self.logger.error("Dev cache clear error: %s", e)
                    return jsonify({"error": str(e)}), 500
    
    def _calculate_daily_average(self, stats):
        """Calculate daily average button presses."""
        try:
            total_presses = stats.get("total_button_presses", 0)
            # Simple calculation based on days since first press
            # In a real implementation, you'd track actual active days
            if total_presses > 0:
                return total_presses / max(1, 7)  # Assuming 7 days for demo
            return 0
        except Exception:
            return 0
    
    def _find_peak_hour(self, stats):
        """Find the hour with most button presses."""
        try:
            today_hourly = stats.get("current_hour", {}).get("button_presses", {})
            if today_hourly:
                peak_hour = max(today_hourly.keys(), key=lambda h: today_hourly[h])
                return f"{peak_hour}:00"
            return "N/A"
        except Exception:
            return "N/A"
    
    def _get_recent_activity(self):
        """Get recent activity list."""
        try:
            # This would ideally come from the statistics manager
            # For now, return a simple placeholder
            return [
                {"action": "Button pressed", "timestamp": "2025-08-09T10:30:00"},
                {"action": "Video played", "timestamp": "2025-08-09T10:29:45"},
                {"action": "Settings updated", "timestamp": "2025-08-09T09:15:22"}
            ]
        except Exception:
            return []
    
    def _register_error_handlers(self):
        """Register error handlers."""
        
        @self.app.errorhandler(404)
        def not_found(_error):
            """Handle 404 errors."""
            return jsonify({"error": "Not found"}), 404
        
        @self.app.errorhandler(413)
        def file_too_large(_error):
            """Handle file too large errors."""
            return jsonify({"error": "File too large"}), 413
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            self.logger.error("Internal server error: %s", error)
            return jsonify({"error": "Internal server error"}), 500
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def run(self, host: str = "0.0.0.0", port: int = None, debug: bool = False):
        """Run the Flask application."""
        if port is None:
            port = getattr(self.config, 'port', 5000)
        
        self.logger.info("Starting web interface on %s:%d", host, port)
        self.app.run(host=host, port=port, debug=debug, threaded=True)
