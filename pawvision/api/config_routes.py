"""Configuration management routes."""

import logging
from flask import Blueprint, request, jsonify
from ..config import PawVisionConfig

config_bp = Blueprint('config', __name__, url_prefix='/api/config')
logger = logging.getLogger(__name__)


def init_config_routes(app_context):
    """Initialize config routes with app context."""
    global config_bp
    config_bp = Blueprint('config', __name__, url_prefix='/api/config')
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

            if not config_manager:
                return jsonify({'success': False, 'message': 'Configuration manager not available'}), 500

            field_map = {
                'gpio_enabled': 'button_enabled',
                'auto_play': 'auto_play',
                'volume': 'volume',
                'playback_duration_minutes': 'playback_duration_minutes',
                'youtube_quality': 'youtube_default_quality',
                'play_schedule': 'play_schedule',
                'night_mode_start': 'night_mode_start',
                'night_mode_end': 'night_mode_end',
                'night_mode_disable_playback': 'night_mode_disable_playback',
                'night_mode_volume': 'night_mode_volume',
                'motion_sensor_enabled': 'motion_sensor_enabled',
                'motion_stop_enabled': 'motion_stop_enabled',
                'motion_stop_timeout_seconds': 'motion_stop_timeout_seconds',
            }
            unknown_fields = set(data) - set(field_map)
            if unknown_fields:
                return jsonify({'success': False, 'message': 'Unsupported configuration fields: ' + ', '.join(sorted(unknown_fields))}), 400

            updates = {field_map[key]: value for key, value in data.items()}
            boolean_fields = {'button_enabled', 'auto_play', 'night_mode_disable_playback', 'motion_sensor_enabled', 'motion_stop_enabled'}
            invalid_boolean = [key for key in boolean_fields if key in updates and not isinstance(updates[key], bool)]
            if invalid_boolean:
                return jsonify({'success': False, 'message': f'{invalid_boolean[0]} must be a boolean'}), 400

            numeric_fields = {
                'volume', 'playback_duration_minutes', 'night_mode_volume',
                'motion_stop_timeout_seconds',
            }
            invalid_number = [
                key for key in numeric_fields
                if key in updates and (isinstance(updates[key], bool) or not isinstance(updates[key], (int, float)))
            ]
            if invalid_number:
                return jsonify({'success': False, 'message': f'{invalid_number[0]} must be a number'}), 400
            if 'play_schedule' in updates and not isinstance(updates['play_schedule'], list):
                return jsonify({'success': False, 'message': 'play_schedule must be a list'}), 400

            # Validate a new instance before persisting or changing the live one.
            new_config = PawVisionConfig(**{**config.to_dict(), **updates})
            config_manager.save_config(new_config)
            for key, value in new_config.to_dict().items():
                setattr(config, key, value)

            logger.info('Configuration updated via API: %s', sorted(data))
            return jsonify({'success': True, 'message': 'Configuration saved successfully'}), 200

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
