"""YouTube integration routes."""

import logging
import math
from threading import Thread
from flask import Blueprint, request, jsonify

youtube_bp = Blueprint('youtube', __name__, url_prefix='/api/youtube')
logger = logging.getLogger(__name__)


def init_youtube_routes(app_context):
    """Initialize YouTube routes with app context."""
    global youtube_bp
    youtube_bp = Blueprint('youtube', __name__, url_prefix='/api/youtube')
    video_player = app_context['video_player']
    download_progress = app_context.get('download_progress', {})

    @youtube_bp.route('/add', methods=['POST'])
    def add_youtube():
        """Add a YouTube video to the library."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            url = data.get('url', '').strip()
            if not url:
                return jsonify({'error': 'YouTube URL is required'}), 400

            if 'youtube.com' not in url and 'youtu.be' not in url:
                return jsonify({'error': 'Invalid YouTube URL'}), 400

            title = data.get('title', '').strip() or None
            try:
                start_time = float(data.get('start_time', 0.0))
                end_offset = data.get('end_offset_seconds')
                end_offset = float(end_offset) if end_offset is not None else None
            except (TypeError, ValueError):
                return jsonify({'error': 'Start time and end offset must be numbers'}), 400
            quality = data.get('quality', '720p')
            download = data.get('download', False)

            if not math.isfinite(start_time) or start_time < 0:
                return jsonify({'error': 'Start time cannot be negative'}), 400

            if end_offset is not None and (not math.isfinite(end_offset) or end_offset < 0):
                return jsonify({'error': 'End offset cannot be negative'}), 400

            success = video_player.library_manager.add_youtube_video(
                url=url,
                custom_title=title,
                custom_start_time=start_time,
                custom_end_offset=end_offset,
                quality=quality,
                download=download,
            )

            if success:
                logger.info('YouTube video added: %s', url)
                return jsonify({
                    'success': True,
                    'status': 'success',
                    'message': 'YouTube video added successfully',
                }), 200
            else:
                error_details = (
                    'Failed to add YouTube video. This could be due to: '
                    '1) YouTube bot detection (try updating yt-dlp: pip install -U yt-dlp), '
                    '2) Invalid video URL or private/unavailable video, '
                    '3) Network issues. '
                    'Check the logs for details or see docs/youtube_troubleshooting.md'
                )
                logger.error('YouTube add failed for URL: %s', url)
                return jsonify({
                    'success': False,
                    'error': error_details,
                    'message': error_details
                }), 500

        except Exception as e:
            logger.error('Add YouTube error: %s', e, exc_info=True)
            error_msg = str(e)
            if 'Sign in' in error_msg or 'bot' in error_msg.lower():
                detailed_msg = 'YouTube bot detection triggered. Update yt-dlp (pip install -U yt-dlp) or add cookies. See docs/youtube_troubleshooting.md for help.'
                return jsonify({
                    'success': False,
                    'error': detailed_msg,
                    'message': detailed_msg
                }), 503
            detailed_msg = f'Failed to add YouTube video: {error_msg}'
            return jsonify({
                'success': False,
                'error': detailed_msg,
                'message': detailed_msg
            }), 500

    @youtube_bp.route('/download', methods=['POST'])
    def download_youtube():
        """Download a YouTube video for offline playback."""
        try:
            data = request.get_json()
            video_path = data.get('path')
            quality = data.get('quality', '720p')

            if not video_path:
                return jsonify({'error': 'Video path is required'}), 400

            video_entry = video_player.library_manager.get_video(video_path)
            if not video_entry or not video_entry.is_youtube:
                return jsonify({'error': 'Video not found or not a YouTube video'}), 400

            def download_task():
                download_id = video_entry.youtube_id
                download_progress[download_id] = {
                    'status': 'starting',
                    'percentage': 0,
                    'video_title': video_entry.get_display_title(),
                }

                def progress_callback(progress_data):
                    download_progress[download_id] = {
                        **progress_data,
                        'video_title': video_entry.get_display_title(),
                    }

                download_path = video_player.library_manager.youtube_manager.download_video(
                    video_entry.youtube_id, quality, progress_callback
                )

                if download_path:
                    video_entry.download_path = download_path
                    video_player.library_manager.add_or_update_video(video_entry)

                    download_progress[download_id] = {
                        'status': 'completed',
                        'percentage': 100,
                        'video_title': video_entry.get_display_title(),
                        'download_path': download_path,
                    }
                else:
                    download_progress[download_id] = {
                        'status': 'error',
                        'percentage': 0,
                        'video_title': video_entry.get_display_title(),
                        'error': 'Download failed',
                    }

            download_thread = Thread(target=download_task, daemon=True)
            download_thread.start()

            return jsonify({
                'status': 'started',
                'message': 'Download started',
                'download_id': video_entry.youtube_id,
            }), 200

        except Exception as e:
            logger.error('Download YouTube error: %s', e)
            return jsonify({'error': 'Download failed'}), 500

    @youtube_bp.route('/validate', methods=['POST'])
    def validate_youtube_url():
        """Validate YouTube URL and fetch title."""
        try:
            data = request.get_json()
            url = data.get('url', '').strip()

            if not url:
                return jsonify({'error': 'URL is required'}), 400

            title, duration = video_player.library_manager.youtube_manager.get_video_title_and_duration(url)

            if title:
                return jsonify({'valid': True, 'title': title, 'duration': duration}), 200
            else:
                return jsonify({
                    'valid': False,
                    'error': 'Invalid YouTube URL or video not accessible',
                }), 400

        except (ValueError, TypeError, OSError) as e:
            logger.error('YouTube URL validation error: %s', e)
            return jsonify({'valid': False, 'error': 'Failed to validate URL'}), 500

    @youtube_bp.route('/download/progress/<download_id>', methods=['GET'])
    def get_download_progress(download_id):
        """Get download progress for a specific video."""
        try:
            progress = download_progress.get(
                download_id,
                {
                    'status': 'not_found',
                    'percentage': 0,
                    'error': 'Download not found',
                },
            )
            return jsonify(progress), 200

        except Exception as e:
            logger.error('Get download progress error: %s', e)
            return jsonify({'error': 'Failed to get progress'}), 500

    @youtube_bp.route('/refresh', methods=['POST'])
    def refresh_youtube_streams():
        """Refresh expired YouTube stream URLs."""
        try:
            count = video_player.library_manager.refresh_youtube_stream_urls()
            return jsonify({'status': 'success', 'refreshed': count}), 200

        except Exception as e:
            logger.error('Refresh YouTube streams error: %s', e)
            return jsonify({'error': 'Refresh failed'}), 500

    return youtube_bp
