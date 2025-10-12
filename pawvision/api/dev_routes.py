"""Development and testing routes."""

import logging
from flask import Blueprint, jsonify

dev_bp = Blueprint('dev', __name__, url_prefix='/dev')
logger = logging.getLogger(__name__)


def init_dev_routes(app_context):
    """Initialize development routes with app context."""
    gpio_manager = app_context.get('gpio_manager')
    video_player = app_context['video_player']

    @dev_bp.route('/button', methods=['POST'])
    def simulate_button():
        """Simulate button press for development."""
        try:
            if gpio_manager:
                gpio_manager.simulate_button_press()
                return jsonify({'success': 'Button press simulated'}), 200
            else:
                return jsonify({'error': 'GPIO manager not available'}), 400
        except Exception as e:
            logger.error('Dev button error: %s', e)
            return jsonify({'error': str(e)}), 500

    @dev_bp.route('/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear video duration cache for development."""
        try:
            video_player.cleanup_cache()
            return jsonify({'success': 'Cache cleared'}), 200
        except Exception as e:
            logger.error('Dev cache clear error: %s', e)
            return jsonify({'error': str(e)}), 500

    return dev_bp
