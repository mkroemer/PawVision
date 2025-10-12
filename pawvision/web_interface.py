"""Web interface for PawVision - Refactored with Blueprints."""

import logging
import os
from datetime import datetime
from flask import Flask, send_from_directory, jsonify
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
        self.app = Flask(__name__, template_folder="../templates", static_folder="../static")

        # Configure Flask
        self.app.config["SECRET_KEY"] = "pawvision-secret-key-change-in-production"
        self.app.config["MAX_CONTENT_LENGTH"] = SecurityValidator.MAX_FILE_SIZE

        # Initialize security
        self.validator = SecurityValidator()
        setup_security_headers(self.app)

        # Register frontend route
        self._register_frontend_route()

        # Register API blueprints
        self._register_blueprints()

        # Register error handlers
        self._register_error_handlers()

    def _register_frontend_route(self):
        """Register the main frontend route for the React SPA."""

        @self.app.route("/")
        @self.app.route("/<path:path>")
        def serve_react_app(path=""):
            """
            Serve the React single-page application.
            
            The React frontend is built with Vite and outputs to static/dist/.
            For development, you can run 'cd frontend && npm run dev' instead.
            """
            dist_dir = os.path.join(self.app.static_folder, "dist")
            
            # Check if the dist directory exists
            if not os.path.exists(dist_dir):
                return """
                <h1>🐾 PawVision Frontend Not Built</h1>
                <p>The React frontend needs to be built before use.</p>
                <h2>To build:</h2>
                <pre>cd frontend && npm run build</pre>
                <h2>Or for development:</h2>
                <pre>cd frontend && npm run dev</pre>
                <p>Then visit <a href="http://localhost:3000">http://localhost:3000</a></p>
                <hr>
                <p><small>Looking for the old interface? It has been replaced with a modern React application.</small></p>
                """, 404
            
            # If the path exists as a file in dist, serve it
            if path and os.path.exists(os.path.join(dist_dir, path)):
                return send_from_directory(dist_dir, path)
            
            # Otherwise, serve index.html for client-side routing
            return send_from_directory(dist_dir, "index.html")
        
        @self.app.route('/thumbnails/<path:filename>')
        def serve_thumbnail(filename):
            """Serve video thumbnail images."""
            thumbnails_dir = os.path.join(os.getcwd(), 'videos', 'thumbnails')
            if os.path.exists(os.path.join(thumbnails_dir, filename)):
                return send_from_directory(thumbnails_dir, filename)
            return '', 404

    def _register_blueprints(self):
        """Register all API blueprints."""
        from .api import (
            video_routes,
            youtube_routes,
            playback_routes,
            config_routes,
            statistics_routes,
            dev_routes,
        )

        # Create app context dict to pass to blueprints
        app_context = {
            'app': self.app,
            'config': self.config,
            'video_player': self.video_player,
            'statistics_manager': self.statistics_manager,
            'gpio_manager': self.gpio_manager,
            'config_manager': self.config_manager,
            'validator': self.validator,
            'download_progress': self.download_progress,
        }

        # Initialize and register each blueprint
        self.logger.info("Registering API blueprints...")
        
        self.app.register_blueprint(video_routes.init_video_routes(app_context))
        self.logger.debug("Registered video routes")
        
        self.app.register_blueprint(youtube_routes.init_youtube_routes(app_context))
        self.logger.debug("Registered YouTube routes")
        
        self.app.register_blueprint(playback_routes.init_playback_routes(app_context))
        self.logger.debug("Registered playback routes")
        
        self.app.register_blueprint(config_routes.init_config_routes(app_context))
        self.logger.debug("Registered config routes")
        
        self.app.register_blueprint(statistics_routes.init_statistics_routes(app_context))
        self.logger.debug("Registered statistics routes")
        
        # Register dev routes only in dev mode
        if getattr(self.config, "dev_mode", False):
            self.app.register_blueprint(dev_routes.init_dev_routes(app_context))
            self.logger.debug("Registered dev routes (dev mode enabled)")
        
        self.logger.info("All API blueprints registered successfully")

    def _register_error_handlers(self):
        """Register error handlers."""

        @self.app.errorhandler(404)
        def not_found(_error):
            """Handle 404 errors."""
            return jsonify({"error": "Not found"}), 404

        @self.app.errorhandler(413)
        def file_too_large(_error):
            """Handle file too large errors."""
            max_size_gb = SecurityValidator.MAX_FILE_SIZE / (1024 * 1024 * 1024)
            return jsonify({
                "error": f"File too large. Maximum upload size is {max_size_gb:.0f}GB",
                "max_size_bytes": SecurityValidator.MAX_FILE_SIZE,
                "max_size_gb": max_size_gb
            }), 413

        @self.app.errorhandler(RequestEntityTooLarge)
        def handle_request_entity_too_large(_error):
            """Handle request entity too large errors."""
            max_size_gb = SecurityValidator.MAX_FILE_SIZE / (1024 * 1024 * 1024)
            return jsonify({
                "error": f"File too large. Maximum upload size is {max_size_gb:.0f}GB",
                "max_size_bytes": SecurityValidator.MAX_FILE_SIZE,
                "max_size_gb": max_size_gb
            }), 413

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            self.logger.error("Internal server error: %s", error)
            return jsonify({"error": "Internal server error"}), 500

    def run(self, host: str = "0.0.0.0", port: int = None, debug: bool = False):
        """Run the Flask application."""
        if port is None:
            port = getattr(self.config, "port", 5000)

        self.logger.info("Starting web interface on %s:%d", host, port)
        self.app.run(host=host, port=port, debug=debug, threaded=True)
