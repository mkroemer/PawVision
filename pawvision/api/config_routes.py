"""Configuration management routes."""

import logging
from flask import Blueprint, request, jsonify

config_bp = Blueprint('config', __name__, url_prefix='/api/config')
logger = logging.getLogger(__name__)


def init_config_routes(app_context):
    """Initialize config routes with app context."""
    config = app_context['config']
    config_manager = app_context.get('config_manager')
    gpio_manager = app_context.get('gpio_manager')

    @config_bp.route('/')
    def get_config():
        """Get current configuration."""
        try:
            config_dict = {
                'gpio_enabled': config.button_enabled,
                'auto_play': getattr(config, 'auto_play', False),
                'volume': config.volume,
                'playback_duration_minutes': getattr(config, 'playback_duration_minutes', 30),
                'youtube_quality': getattr(config, 'youtube_default_quality', '720p'),
                'play_schedule': config.play_schedule or [],
                'night_mode_start': config.night_mode_start,
                'night_mode_end': config.night_mode_end,
                'night_mode_disable_playback': config.night_mode_disable_playback,
                'night_mode_volume': getattr(config, 'night_mode_volume', 30),
                'motion_sensor_enabled': config.motion_sensor_enabled,
                'motion_stop_enabled': config.motion_stop_enabled,
                'motion_stop_timeout_seconds': config.motion_stop_timeout_seconds,
            }
            return jsonify({'success': True, 'data': config_dict}), 200
        except Exception as e:
            logger.error('API config get error: %s', e)
            return jsonify({'success': False, 'message': 'Failed to get configuration'}), 500

    @config_bp.route('/update', methods=['POST'])
    def update_config():
        """Update configuration."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400

            logger.info('Received config update request with data: %s', data)

            # Update config values
            if 'gpio_enabled' in data:
                config.button_enabled = data['gpio_enabled']
            if 'auto_play' in data:
                config.auto_play = bool(data['auto_play'])
            if 'volume' in data:
                config.volume = max(0, min(100, int(data['volume'])))
            if 'playback_duration_minutes' in data:
                config.playback_duration_minutes = max(1, min(120, int(data['playback_duration_minutes'])))
            if 'youtube_quality' in data:
                config.youtube_default_quality = data['youtube_quality']
            if 'play_schedule' in data:
                # Validate and set play_schedule as a list of time strings
                schedule = data['play_schedule']
                logger.debug('Received play_schedule: %s (type: %s)', schedule, type(schedule))
                if isinstance(schedule, list):
                    # Filter out empty strings and invalid values
                    filtered_schedule = [t for t in schedule if t and isinstance(t, str) and t.strip()]
                    logger.debug('Filtered play_schedule: %s', filtered_schedule)
                    config.play_schedule = filtered_schedule
                else:
                    config.play_schedule = []
            if 'night_mode_start' in data:
                config.night_mode_start = data['night_mode_start']
            if 'night_mode_end' in data:
                config.night_mode_end = data['night_mode_end']
            if 'night_mode_disable_playback' in data:
                config.night_mode_disable_playback = data['night_mode_disable_playback']
            if 'night_mode_volume' in data:
                config.night_mode_volume = max(0, min(100, int(data['night_mode_volume'])))
            if 'motion_sensor_enabled' in data:
                config.motion_sensor_enabled = data['motion_sensor_enabled']
            if 'motion_stop_enabled' in data:
                config.motion_stop_enabled = data['motion_stop_enabled']
            if 'motion_stop_timeout_seconds' in data:
                config.motion_stop_timeout_seconds = int(data['motion_stop_timeout_seconds'])

            # Save configuration
            if config_manager:
                config_manager.save_config(config)
                logger.info('Configuration updated via API')
                return jsonify({'success': True, 'message': 'Configuration saved successfully'}), 200
            else:
                return jsonify({'success': False, 'message': 'Configuration manager not available'}), 500

        except ValueError as e:
            # Configuration validation error - extract the specific field that failed
            error_msg = str(e)
            logger.error('Configuration validation error: %s', error_msg, exc_info=True)
            
            # Try to make the error message more user-friendly
            if 'Invalid time format' in error_msg:
                error_msg = 'The string did not match the expected pattern. Please use HH:MM format (e.g., 09:00) for all time fields.'
            
            return jsonify({'success': False, 'error': error_msg, 'message': error_msg}), 400
        except Exception as e:
            logger.error('API config update error: %s', e, exc_info=True)
            return jsonify({'success': False, 'message': f'Failed to update configuration: {str(e)}'}), 500

    @config_bp.route('/reset', methods=['POST'])
    def reset_config():
        """Reset configuration to defaults."""
        try:
            if config_manager:
                # Reset to default config
                from ..config import PawVisionConfig
                new_config = PawVisionConfig()
                config_manager.save_config(new_config)
                
                # Update the reference
                for key, value in new_config.to_dict().items():
                    setattr(config, key, value)
                
                logger.info('Configuration reset to defaults')
                return jsonify({'success': True, 'message': 'Configuration reset to defaults'}), 200
            else:
                return jsonify({'success': False, 'message': 'Configuration manager not available'}), 500
        except Exception as e:
            logger.error('API config reset error: %s', e)
            return jsonify({'success': False, 'message': 'Failed to reset configuration'}), 500

    @config_bp.route('/test-gpio', methods=['POST'])
    def test_gpio():
        """Test GPIO button."""
        try:
            if gpio_manager and config.button_enabled:
                # Simulate button press
                logger.info('GPIO test triggered via API')
                return jsonify({'success': True, 'message': 'GPIO test completed'}), 200
            else:
                return jsonify({'success': False, 'message': 'GPIO not enabled or not available'}), 400
        except Exception as e:
            logger.error('API GPIO test error: %s', e)
            return jsonify({'success': False, 'message': 'GPIO test failed'}), 500

    return config_bp
