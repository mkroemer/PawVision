"""Shared setup helpers for Flask web application wiring."""

from flask import jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from .security import SecurityValidator


def create_app_context(
    app,
    config,
    video_player,
    statistics_manager,
    gpio_manager,
    config_manager,
    validator,
    download_progress,
):
    """Create a context dictionary shared with API route modules."""
    return {
        "app": app,
        "config": config,
        "video_player": video_player,
        "statistics_manager": statistics_manager,
        "gpio_manager": gpio_manager,
        "config_manager": config_manager,
        "validator": validator,
        "download_progress": download_progress,
    }


def register_api_blueprints(app, app_context, logger):
    """Register API blueprints, binding each one to this app's context.

    Each ``init_*`` helper builds and returns a fresh Blueprint whose view
    functions close over ``app_context``, so it must run once per app.  Reusing
    a previously built blueprint would bind this app to another app's
    video_player/statistics_manager.
    """
    from .api import (
        config_routes,
        dev_routes,
        playback_routes,
        statistics_routes,
        stream_routes,
        video_routes,
        youtube_routes,
    )

    blueprint_specs = [
        ("video", video_routes, "init_video_routes", True),
        ("youtube", youtube_routes, "init_youtube_routes", True),
        ("playback", playback_routes, "init_playback_routes", True),
        ("config", config_routes, "init_config_routes", True),
        ("statistics", statistics_routes, "init_statistics_routes", True),
        ("stream", stream_routes, "init_stream_routes", True),
        (
            "dev",
            dev_routes,
            "init_dev_routes",
            bool(getattr(app_context["config"], "dev_mode", False)),
        ),
    ]

    logger.info("Registering API blueprints...")
    for name, module, init_name, enabled in blueprint_specs:
        if not enabled:
            continue

        blueprint = getattr(module, init_name)(app_context)
        app.register_blueprint(blueprint)
        logger.debug("Registered %s routes", name)

    logger.info("All API blueprints registered successfully")


def register_error_handlers(app, logger):
    """Register shared 404/413/500 Flask error handlers."""

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(413)
    def file_too_large(_error):
        max_size_gb = SecurityValidator.MAX_FILE_SIZE / (1024 * 1024 * 1024)
        return jsonify(
            {
                "error": f"File too large. Maximum upload size is {max_size_gb:.0f}GB",
                "max_size_bytes": SecurityValidator.MAX_FILE_SIZE,
                "max_size_gb": max_size_gb,
            }
        ), 413

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(_error):
        max_size_gb = SecurityValidator.MAX_FILE_SIZE / (1024 * 1024 * 1024)
        return jsonify(
            {
                "error": f"File too large. Maximum upload size is {max_size_gb:.0f}GB",
                "max_size_bytes": SecurityValidator.MAX_FILE_SIZE,
                "max_size_gb": max_size_gb,
            }
        ), 413

    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal server error: %s", error)
        return jsonify({"error": "Internal server error"}), 500
