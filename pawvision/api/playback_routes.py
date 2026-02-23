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
            success = video_player.stop_video(reason='web')

            if statistics_manager:
                statistics_manager.record_api_call('stop')

            if success:
                return jsonify({'status': 'success'}), 200
            else:
                return jsonify({'status': 'success', 'message': 'No video was playing'}), 200

        except Exception as e:
            logger.error('Stop error: %s', e)
            return jsonify({'error': 'Stop failed'}), 500

    @playback_bp.route('/next', methods=['POST'])
    def api_next():
        """Stop current playback and start next random video."""
        try:
            if video_player.is_playing():
                video_player.stop_video(reason='web-next')

            success = video_player.play_random_video(trigger='web-next')
            if statistics_manager:
                statistics_manager.record_api_call('next')

            if success:
                return jsonify({'status': 'success'}), 200
            return jsonify({'error': 'Failed to start next video'}), 500
        except Exception as e:
            logger.error('Next error: %s', e)
            return jsonify({'error': 'Next failed'}), 500

    @playback_bp.route('/pause', methods=['POST'])
    def api_pause():
        """Pause playback."""
        try:
            success = video_player.pause_video()

            if statistics_manager:
                statistics_manager.record_api_call('pause')

            if success:
                return jsonify({'status': 'success'}), 200
            else:
                return jsonify({'error': 'Failed to pause video'}), 500

        except Exception as e:
            logger.error('Pause error: %s', e)
            return jsonify({'error': 'Pause failed'}), 500

    @playback_bp.route('/resume', methods=['POST'])
    def api_resume():
        """Resume playback."""
        try:
            success = video_player.resume_video()

            if statistics_manager:
                statistics_manager.record_api_call('resume')

            if success:
                return jsonify({'status': 'success'}), 200
            else:
                return jsonify({'error': 'Failed to resume video'}), 500

        except Exception as e:
            logger.error('Resume error: %s', e)
            return jsonify({'error': 'Resume failed'}), 500

    @playback_bp.route('/volume', methods=['POST'])
    def api_volume():
        """Set volume."""
        try:
            volume = request.form.get('volume') or (request.json.get('volume') if request.json else None)
            
            if volume is None:
                return jsonify({'error': 'No volume value provided'}), 400

            try:
                volume = int(volume)
            except (ValueError, TypeError):
                return jsonify({'error': 'Volume must be an integer (0-100)'}), 400

            if not 0 <= volume <= 100:
                return jsonify({'error': 'Volume must be between 0 and 100'}), 400

            success = video_player.set_volume(volume)

            if statistics_manager:
                statistics_manager.record_api_call('volume')

            if success:
                return jsonify({'status': 'success', 'volume': volume}), 200
            else:
                return jsonify({'error': 'Failed to set volume'}), 500

        except Exception as e:
            logger.error('Volume error: %s', e)
            return jsonify({'error': 'Volume control failed'}), 500

    @playback_bp.route('/status')
    def api_status():
        """Get playback status."""
        try:
            is_playing = video_player.is_playing()
            is_paused = video_player.is_paused()
            current_video = video_player.get_current_video_info()

            logger.debug("Status check - playing: %s, paused: %s, current_video: %s", 
                        is_playing, is_paused, current_video is not None)

            return jsonify({
                'playing': is_playing,
                'is_playing': is_playing,  # Support both field names
                'paused': is_paused,
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
