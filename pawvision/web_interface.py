"""Web interface for PawVision - Refactored with Blueprints."""

import logging
import os
import secrets
import hmac
from flask import Flask, jsonify, request, send_from_directory

from .security import SecurityValidator, setup_security_headers
from .web_setup import create_app_context, register_api_blueprints, register_error_handlers


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
        self.app.config["SECRET_KEY"] = os.getenv(
            "PAWVISION_SECRET_KEY",
            getattr(self.config, "secret_key", None) or secrets.token_urlsafe(32),
        )
        self.app.config["MAX_CONTENT_LENGTH"] = SecurityValidator.MAX_FILE_SIZE
        self.api_token = os.environ.get("PAWVISION_API_TOKEN")

        # Initialize security
        self.validator = SecurityValidator()
        setup_security_headers(self.app)
        self._register_api_authentication()

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

    def _register_api_authentication(self):
        """Protect mutating API requests when a deployment token is configured."""
        @self.app.before_request
        def require_api_token():
            if (
                not self.api_token
                or not request.path.startswith("/api/")
                or request.method in {"GET", "HEAD", "OPTIONS"}
            ):
                return None

            supplied_token = request.headers.get("X-PawVision-Token", "")
            if not hmac.compare_digest(supplied_token, self.api_token):
                return jsonify({"error": "Authentication required"}), 401
            return None

    def _register_blueprints(self):
        """Register all API blueprints."""
        app_context = create_app_context(
            app=self.app,
            config=self.config,
            video_player=self.video_player,
            statistics_manager=self.statistics_manager,
            gpio_manager=self.gpio_manager,
            config_manager=self.config_manager,
            validator=self.validator,
            download_progress=self.download_progress,
        )
        register_api_blueprints(self.app, app_context, self.logger)

    def _register_error_handlers(self):
        """Register error handlers."""
        register_error_handlers(self.app, self.logger)

    def run(self, host: str = "0.0.0.0", port: int = None, debug: bool = False):
        """Run the Flask application."""
        if port is None:
            port = getattr(self.config, "port", 5000)

        self.logger.info("Starting web interface on %s:%d", host, port)
        self.app.run(host=host, port=port, debug=debug, threaded=True)
