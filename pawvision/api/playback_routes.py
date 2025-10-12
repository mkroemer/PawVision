"""Playback control routes."""

import logging
from flask import Blueprint, request, jsonify

playback_bp = Blueprint('playback', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


def init_playback_routes(app_context):
    """Initialize playback routes with app context."""
    video_player = app_context['video_player']
    statistics_manager = app_context.get('statistics_manager')

    @playback_bp.route('/play', methods=['POST'])
    def api_play():
        """Play a video."""
        try:
            video_path = request.form.get('path')
            if not video_path:
                return jsonify({'error': 'No video path provided'}), 400

            success = video_player.play_video(video_path, triggered_by='web')

            if success:
                if statistics_manager:
                    statistics_manager.record_api_call('play')
                return jsonify({'status': 'success'}), 200
            else:
                return jsonify({'error': 'Failed to start playback'}), 500

        except Exception as e:
            logger.error('Play error: %s', e)
            return jsonify({'error': 'Play failed'}), 500

    @playback_bp.route('/stop', methods=['POST'])
    def api_stop():
        """Stop playback."""
        try:
            video_player.stop_playback()

            if statistics_manager:
                statistics_manager.record_api_call('stop')

            return jsonify({'status': 'success'}), 200

        except Exception as e:
            logger.error('Stop error: %s', e)
            return jsonify({'error': 'Stop failed'}), 500

    @playback_bp.route('/status')
    def api_status():
        """Get playback status."""
        try:
            is_playing = video_player.is_playing()
            current_video = video_player.get_current_video()

            return jsonify({
                'playing': is_playing,
                'current_video': current_video,
            }), 200

        except Exception as e:
            logger.error('Status error: %s', e)
            return jsonify({'error': 'Failed to get status'}), 500

    @playback_bp.route('/health')
    def api_health():
        """Health check endpoint."""
        try:
            return jsonify({
                'status': 'healthy',
                'video_player': 'ok',
            }), 200

        except Exception as e:
            logger.error('Health check error: %s', e)
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
            }), 500

    @playback_bp.route('/current-video')
    def api_current_video():
        """Get currently playing video details."""
        try:
            current_video = video_player.get_current_video()

            if current_video:
                return jsonify({
                    'success': True,
                    'video': current_video,
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'No video currently playing',
                }), 200

        except Exception as e:
            logger.error('Current video error: %s', e)
            return jsonify({
                'success': False,
                'message': 'Failed to get current video',
            }), 500

    return playback_bp
