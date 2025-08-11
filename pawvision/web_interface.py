"""Web interface for PawVision."""

import logging
import os
from datetime import datetime
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
        
        # Download progress tracking
        self.download_progress = {}
        
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
            """Main SPA dashboard page with all content."""
            try:
                # Get data for all tabs
                videos = self.video_player.get_video_library_entries()
                # Create a simple status object
                status = {
                    'is_playing': self.video_player.is_playing(),
                    'next_scheduled_play': None  # Add scheduling logic later if needed
                }
                recent_videos = videos[-5:] if videos else []  # Last 5 videos
                
                # Get basic statistics
                stats = {}
                recent_activity = []
                if self.statistics_manager:
                    stats = self.statistics_manager.get_summary()
                    # Mock recent activity for now
                    recent_activity = []
                
                # Get configuration settings
                settings = self.config.to_dict()
                
                return render_template("dashboard.html", 
                                     videos=videos,
                                     status=status,
                                     recent_videos=recent_videos,
                                     stats=stats,
                                     recent_activity=recent_activity,
                                     settings=settings)
            except (OSError, ValueError) as e:
                self.logger.error("Error rendering index page: %s", e)
                return "Internal server error", 500
        
        @self.app.route("/api/video/upload", methods=["POST"])
        def api_upload_video():
            """API endpoint to upload a video file."""
            try:
                if 'file' not in request.files:
                    return jsonify({"success": False, "message": "No file selected"}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({"success": False, "message": "No file selected"}), 400
                
                # Validate file
                is_valid, result = self.validator.validate_video_file(file)
                if not is_valid:
                    return jsonify({"success": False, "message": result}), 400
                
                # result contains the sanitized filename
                filename = result
                file_path = os.path.join(self.config.video_directory, filename)
                
                # Ensure directory exists
                os.makedirs(self.config.video_directory, exist_ok=True)
                
                file.save(file_path)
                self.logger.info("File uploaded: %s", filename)
                
                # Update statistics
                if self.statistics_manager:
                    self.statistics_manager.record_api_call("upload")
                
                return jsonify({"success": True, "message": f"File '{filename}' uploaded successfully", "filename": filename}), 200
                
            except Exception as e:
                self.logger.error("Upload error: %s", e)
                return jsonify({"success": False, "message": "Upload failed"}), 500
        
        @self.app.route("/api/video/library")
        def api_video_library():
            """API endpoint to get video library data."""
            try:
                videos = self.video_player.get_video_library_entries()
                return jsonify({"success": True, "videos": videos}), 200
            except Exception as e:
                self.logger.error("Error getting video library: %s", e)
                return jsonify({"success": False, "message": "Failed to get video library"}), 500
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
        
        @self.app.route("/api/video/delete", methods=["POST"])
        def delete_video():
            """Handle video file deletion."""
            try:
                video_path = request.form.get("path")
                if not video_path:
                    return jsonify({"error": "No file path provided"}), 400
                
                # Handle YouTube videos - remove from library and delete downloaded files
                if video_path.startswith("youtube://"):
                    # Get video entry first to check for downloaded file
                    video_entry = self.video_player.library_manager.get_video(video_path)
                    downloaded_file_deleted = False
                    
                    if video_entry and video_entry.download_path and os.path.exists(video_entry.download_path):
                        try:
                            os.remove(video_entry.download_path)
                            downloaded_file_deleted = True
                            self.logger.info("Deleted downloaded file: %s", video_entry.download_path)
                        except OSError as e:
                            self.logger.error("Failed to delete downloaded file %s: %s", video_entry.download_path, e)
                    
                    # Remove from library database
                    success = self.video_player.library_manager.remove_video(video_path)
                    if success:
                        message = "YouTube video removed from library"
                        if downloaded_file_deleted:
                            message += " and downloaded file deleted"
                        return jsonify({"success": message}), 200
                    else:
                        return jsonify({"error": "Failed to remove YouTube video"}), 500
                
                # Validate regular file path
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
                # Redirect back to the config page with success parameter
                return redirect("/config?saved=1")
            
            except ValueError as e:
                self.logger.error("Settings validation error: %s", e)
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                self.logger.error("Settings update error: %s", e)
                return jsonify({"error": "Settings update failed"}), 500
        
        @self.app.route("/api/video/update", methods=["POST"])
        def update_video():
            """Handle video metadata update."""
            try:
                video_path = request.form.get("path")
                title = request.form.get("title", "").strip()
                custom_start_time = request.form.get("custom_start_time")
                custom_end_offset = request.form.get("custom_end_offset")  # Changed from custom_end_time
                
                if not video_path:
                    return jsonify({"error": "No file path provided"}), 400
                
                # Handle YouTube videos differently from regular files
                is_youtube = video_path.startswith("youtube://")
                
                if is_youtube:
                    # For YouTube videos, just validate the format
                    if not video_path.startswith("youtube://") or len(video_path.split("://")) != 2:
                        return jsonify({"error": "Invalid YouTube video path"}), 400
                else:
                    # Validate regular file path
                    if not self.validator.validate_file_path(video_path, self.video_player.video_dirs):
                        return jsonify({"error": "Invalid file path"}), 400
                    
                    if not os.path.exists(video_path):
                        return jsonify({"error": "File not found"}), 404
                
                # Get video entry to access duration
                video_entry = self.video_player.get_video_entry(video_path)
                if not video_entry or not video_entry.duration:
                    return jsonify({"error": "Could not get video duration"}), 400
                
                # Parse and validate times
                start_time = None
                end_time = None
                
                if custom_start_time:
                    try:
                        start_time = float(custom_start_time)
                        if start_time < 0:
                            return jsonify({"error": "Start time cannot be negative"}), 400
                        if start_time >= video_entry.duration:
                            return jsonify({"error": "Start time cannot be greater than video duration"}), 400
                    except ValueError:
                        return jsonify({"error": "Invalid start time format"}), 400
                
                if custom_end_offset:
                    try:
                        end_offset = float(custom_end_offset)
                        if end_offset <= 0:
                            return jsonify({"error": "End offset must be positive"}), 400
                        if end_offset >= video_entry.duration:
                            return jsonify({"error": "End offset cannot be greater than video duration"}), 400
                        
                        # Convert offset to absolute end time
                        end_time = video_entry.duration - end_offset
                        
                        if start_time is not None and end_time <= start_time:
                            return jsonify({"error": "End time must be after start time"}), 400
                    except ValueError:
                        return jsonify({"error": "Invalid end offset format"}), 400
                
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
                    return redirect(url_for('index') + '#playlist')
                else:
                    return jsonify({"error": "Failed to update video metadata"}), 500
                
            except Exception as e:
                self.logger.error("Video update error: %s", e)
                return jsonify({"error": "Update failed"}), 500
        
        # YouTube Routes
        @self.app.route("/api/youtube/add", methods=["POST"])
        def add_youtube():
            """Add a YouTube video to the library."""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({"error": "No data provided"}), 400
                
                url = data.get('url', '').strip()
                if not url:
                    return jsonify({"error": "YouTube URL is required"}), 400
                
                # Validate it's a YouTube URL
                if 'youtube.com' not in url and 'youtu.be' not in url:
                    return jsonify({"error": "Invalid YouTube URL"}), 400
                
                title = data.get('title') or ''
                title = title.strip() if title else ''
                start_time = data.get('start_time', 0.0)
                end_time = data.get('end_time')
                quality = data.get('quality', '720p')
                download = data.get('download', False)
                
                # Validate start time
                if start_time < 0:
                    return jsonify({"error": "Start time cannot be negative"}), 400
                
                # Validate end time if provided
                if end_time is not None:
                    if end_time <= start_time:
                        return jsonify({"error": "End time must be after start time"}), 400
                
                # Add to library
                success = self.video_player.library_manager.add_youtube_video(
                    url=url,
                    custom_title=title if title else None,
                    custom_start_time=start_time,
                    custom_end_offset=end_time,  # Changed to custom_end_offset for relative timing
                    quality=quality,
                    download=download
                )
                
                if success:
                    self.logger.info("YouTube video added: %s", url)
                    return jsonify({"status": "success", "message": "YouTube video added successfully"}), 200
                else:
                    return jsonify({"error": "Failed to add YouTube video"}), 500
                
            except Exception as e:
                self.logger.error("Add YouTube error: %s", e)
                return jsonify({"error": "Failed to add YouTube video"}), 500
        
        @self.app.route("/api/youtube/download", methods=["POST"])
        def download_youtube():
            """Download a YouTube video for offline playback."""
            try:
                data = request.get_json()
                video_path = data.get('path')
                quality = data.get('quality', '720p')
                
                if not video_path:
                    return jsonify({"error": "Video path is required"}), 400
                
                # Get video entry to extract YouTube ID
                video_entry = self.video_player.library_manager.get_video(video_path)
                if not video_entry or not video_entry.is_youtube:
                    return jsonify({"error": "Video not found or not a YouTube video"}), 400
                
                # Start download in background and return immediately
                from threading import Thread
                
                def download_task():
                    # Store progress in a simple dict (in production, use Redis or similar)
                    download_id = video_entry.youtube_id
                    self.download_progress[download_id] = {
                        'status': 'starting',
                        'percentage': 0,
                        'video_title': video_entry.get_display_title()
                    }
                    
                    def progress_callback(progress_data):
                        self.download_progress[download_id] = {
                            **progress_data,
                            'video_title': video_entry.get_display_title()
                        }
                    
                    # Perform download
                    download_path = self.video_player.library_manager.youtube_manager.download_video(
                        video_entry.youtube_id, quality, progress_callback
                    )
                    
                    if download_path:
                        # Update video entry
                        video_entry.download_path = download_path
                        video_entry.updated_at = datetime.now().isoformat()
                        self.video_player.library_manager.add_or_update_video(video_entry)
                        
                        self.download_progress[download_id] = {
                            'status': 'completed',
                            'percentage': 100,
                            'video_title': video_entry.get_display_title(),
                            'download_path': download_path
                        }
                    else:
                        self.download_progress[download_id] = {
                            'status': 'error',
                            'percentage': 0,
                            'video_title': video_entry.get_display_title(),
                            'error': 'Download failed'
                        }
                
                # Start download thread
                download_thread = Thread(target=download_task, daemon=True)
                download_thread.start()
                
                return jsonify({
                    "status": "started", 
                    "message": "Download started",
                    "download_id": video_entry.youtube_id
                }), 200
                
            except Exception as e:
                self.logger.error("Download YouTube error: %s", e)
                return jsonify({"error": "Download failed"}), 500
        
        @self.app.route("/api/youtube/validate", methods=["POST"])
        def validate_youtube_url():
            """Validate YouTube URL and fetch title."""
            try:
                data = request.get_json()
                url = data.get('url', '').strip()
                
                if not url:
                    return jsonify({"error": "URL is required"}), 400
                
                # Get title and duration
                title, duration = self.video_player.library_manager.youtube_manager.get_video_title_and_duration(url)
                
                if title:
                    return jsonify({
                        "valid": True,
                        "title": title,
                        "duration": duration
                    }), 200
                else:
                    return jsonify({
                        "valid": False,
                        "error": "Invalid YouTube URL or video not accessible"
                    }), 400
                
            except (ValueError, TypeError, OSError) as e:
                self.logger.error("YouTube URL validation error: %s", e)
                return jsonify({
                    "valid": False,
                    "error": "Failed to validate URL"
                }), 500

        @self.app.route("/api/youtube/download/progress/<download_id>", methods=["GET"])
        def get_download_progress(download_id):
            """Get download progress for a specific video."""
            try:
                progress = self.download_progress.get(download_id, {
                    'status': 'not_found',
                    'percentage': 0,
                    'error': 'Download not found'
                })
                return jsonify(progress), 200
                
            except Exception as e:
                self.logger.error("Get download progress error: %s", e)
                return jsonify({"error": "Failed to get progress"}), 500
        
        @self.app.route("/api/youtube/refresh", methods=["POST"])
        def refresh_youtube_streams():
            """Refresh expired YouTube stream URLs."""
            try:
                count = self.video_player.library_manager.refresh_youtube_stream_urls()
                return jsonify({"status": "success", "refreshed": count}), 200
                
            except Exception as e:
                self.logger.error("Refresh YouTube streams error: %s", e)
                return jsonify({"error": "Refresh failed"}), 500
        
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
                
                period = request.args.get('period', '24h')
                stats = self.statistics_manager.get_summary()
                
                # Check if motion sensor/GPIO is enabled
                motion_sensor_enabled = hasattr(self, 'gpio_manager') and self.gpio_manager is not None
                
                # Calculate average watch time from button press events
                avg_watch_time_str = "0m"
                if motion_sensor_enabled and 'button_presses' in stats:
                    avg_watch_time = self.statistics_manager.get_average_watch_time()
                    if avg_watch_time > 0:
                        if avg_watch_time >= 60:
                            minutes = int(avg_watch_time // 60)
                            seconds = int(avg_watch_time % 60)
                            avg_watch_time_str = f"{minutes}m {seconds}s" if seconds > 0 else f"{minutes}m"
                        else:
                            avg_watch_time_str = f"{int(avg_watch_time)}s"
                
                frontend_response = {
                    "status": "success",
                    "stats": {
                        "total_plays": stats.get("button_presses", {}).get("total", 0) if motion_sensor_enabled else stats.get("video_plays", {}).get("total", 0),
                        "total_watch_time_str": f"{stats.get('video_viewing', {}).get('total_duration', 0)/60:.0f}m",
                        "avg_daily_plays": stats.get("button_presses", {}).get("daily_average", 0) if motion_sensor_enabled else 0,
                        "motion_sensor_enabled": motion_sensor_enabled,
                        "avg_watch_time_str": avg_watch_time_str,
                        "plays_trend": 0,
                        "duration_trend": 0
                    },
                    "charts": {
                        "plays": {
                            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                            "data": [5, 8, 3, 12, 7, 4, 9]
                        }
                    },
                    "activity": []
                }
                
                return jsonify(frontend_response), 200
            
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
        
        @self.app.route("/api/statistics/export")
        def api_export_statistics():
            """API endpoint to export statistics data."""
            try:
                if not self.statistics_manager:
                    return jsonify({"error": "Statistics not enabled"}), 404
                
                format_type = request.args.get('format', 'json').lower()
                stats = self.statistics_manager.get_summary()
                
                if format_type == 'csv':
                    # Create a simple CSV export (this would need proper CSV formatting in production)
                    csv_data = "metric,value\n"
                    for key, value in stats.items():
                        csv_data += f"{key},{value}\n"
                    
                    response = self.app.response_class(
                        csv_data,
                        mimetype='text/csv',
                        headers={"Content-Disposition": "attachment; filename=pawvision-stats.csv"}
                    )
                    return response
                else:
                    # JSON export
                    response = self.app.response_class(
                        jsonify(stats).data,
                        mimetype='application/json',
                        headers={"Content-Disposition": "attachment; filename=pawvision-stats.json"}
                    )
                    return response
                    
            except Exception as e:
                self.logger.error("API export statistics error: %s", e)
                return jsonify({"error": "Internal error"}), 500
        
        @self.app.route("/api/statistics/report")
        def api_generate_report():
            """API endpoint to generate statistics report."""
            try:
                if not self.statistics_manager:
                    return jsonify({"error": "Statistics not enabled"}), 404
                
                stats = self.statistics_manager.get_summary()
                
                # Generate a simple HTML report
                report_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>PawVision Statistics Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                    </style>
                </head>
                <body>
                    <h1>PawVision Statistics Report</h1>
                    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <table>
                        <tr><th>Metric</th><th>Value</th></tr>
                """
                
                for key, value in stats.items():
                    report_html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
                
                report_html += """
                    </table>
                </body>
                </html>
                """
                
                response = self.app.response_class(
                    report_html,
                    mimetype='text/html',
                    headers={"Content-Disposition": "attachment; filename=pawvision-report.html"}
                )
                return response
                    
            except Exception as e:
                self.logger.error("API generate report error: %s", e)
                return jsonify({"error": "Internal error"}), 500
        
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
        return datetime.now().isoformat()
    
    def run(self, host: str = "0.0.0.0", port: int = None, debug: bool = False):
        """Run the Flask application."""
        if port is None:
            port = getattr(self.config, 'port', 5000)
        
        self.logger.info("Starting web interface on %s:%d", host, port)
        self.app.run(host=host, port=port, debug=debug, threaded=True)
