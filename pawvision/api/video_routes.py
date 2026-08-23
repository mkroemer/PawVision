"""Video library management routes."""

import logging
import os
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

video_bp = Blueprint('video', __name__, url_prefix='/api/video')
logger = logging.getLogger(__name__)


def init_video_routes(app_context):
    """Initialize video routes with app context.
    
    Args:
        app_context: Dict with 'video_player', 'validator', 'statistics_manager', 'config'
    """
    global video_bp
    video_bp = Blueprint('video', __name__, url_prefix='/api/video')
    video_player = app_context['video_player']
    validator = app_context['validator']
    statistics_manager = app_context.get('statistics_manager')
    config = app_context['config']

    @video_bp.route('/upload', methods=['POST'])
    def upload_video():
        """Handle video file upload."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file selected'}), 400

            file = request.files['file']

            # Validate file
            valid, result = validator.validate_video_file(file)
            if not valid:
                return jsonify({'error': result}), 400

            filename = result

            # Get upload directory
            video_dirs = [d for d in video_player.video_dirs if os.path.exists(d)]
            if not video_dirs:
                return jsonify({'error': 'No video directory available'}), 500

            upload_dir = video_dirs[0]
            save_path = os.path.join(upload_dir, filename)

            # Check if file already exists
            if os.path.exists(save_path):
                return jsonify({
                    'error': f'A video named "{filename}" already exists in the library. Please rename your file or delete the existing video first.'
                }), 409

            # Save file
            file.save(save_path)

            # Update statistics
            if statistics_manager:
                statistics_manager.record_api_call('upload')

            logger.info('Video uploaded: %s', filename)
            return jsonify({'success': f'Uploaded {filename}'}), 200

        except RequestEntityTooLarge:
            from ..security import SecurityValidator
            max_size_gb = SecurityValidator.MAX_FILE_SIZE / (1024 * 1024 * 1024)
            return jsonify({
                'error': f'File too large. Maximum upload size is {max_size_gb:.0f}GB',
                'max_size_gb': max_size_gb
            }), 413
        except OSError as e:
            logger.error('Upload error: %s', e)
            return jsonify({'error': 'Upload failed'}), 500

    @video_bp.route('/library')
    def video_library():
        """Get video library data."""
        try:
            videos = video_player.get_video_library_entries()
            return jsonify({'success': True, 'videos': videos}), 200
        except Exception as e:
            logger.error('Error getting video library: %s', e)
            return jsonify({'success': False, 'message': 'Failed to get video library'}), 500

    @video_bp.route('/list')
    def list_videos():
        """Get video list (alias for /library for frontend compatibility)."""
        try:
            page = request.args.get('page', type=int)
            per_page = request.args.get('per_page', type=int)
            paginated = request.args.get('paginated', '').lower() in ('1', 'true', 'yes') or page is not None or per_page is not None

            video_entries = video_player.get_video_library_entries()
            total = len(video_entries)

            if page is not None or per_page is not None:
                page = max(1, page or 1)
                per_page = max(1, min(100, per_page or 20))
                start = (page - 1) * per_page
                end = start + per_page
                video_entries = video_entries[start:end]

            # Transform VideoEntry objects to match frontend expected format
            video_list = []
            for idx, entry in enumerate(video_entries):
                # Get filename from path
                if entry.is_youtube:
                    filename = f"{entry.youtube_id}.mp4" if entry.youtube_id else "youtube_video.mp4"
                else:
                    filename = os.path.basename(entry.path)
                
                # Convert thumbnail path to URL (don't generate on-demand, too slow)
                thumbnail_url = None
                if entry.thumbnail_path and os.path.exists(entry.thumbnail_path):
                    # Serve thumbnails as static files from /thumbnails/
                    thumbnail_url = f"/thumbnails/{os.path.basename(entry.thumbnail_path)}"
                
                video_list.append({
                    'id': idx + 1 + (((page - 1) * per_page) if page and per_page else 0),  # Generate stable IDs for paged data
                    'title': entry.get_display_title(),
                    'filename': filename,
                    'path': entry.path,  # Include path for edit operations
                    'duration': entry.duration or 0,
                    'size': entry.size or 0,
                    'source': 'youtube' if entry.is_youtube else 'local',
                    'youtube_url': entry.youtube_url,
                    'youtube_id': entry.youtube_id,
                    'download_path': entry.download_path,
                    'thumbnail': thumbnail_url,
                    'added_date': entry.added_time.isoformat() if entry.added_time else '',
                    'custom_start_time': entry.custom_start_time,
                    'custom_end_time': entry.custom_end_time
                })

            if paginated:
                return jsonify({
                    'success': True,
                    'videos': video_list,
                    'pagination': {
                        'page': page or 1,
                        'per_page': per_page or total,
                        'total': total,
                        'has_more': bool(page and per_page and (page * per_page) < total),
                    },
                }), 200

            return jsonify(video_list), 200
        except Exception as e:
            logger.error('Error getting video list: %s', e)
            return jsonify({'error': 'Failed to get video list'}), 500

    @video_bp.route('/delete', methods=['POST'])
    def delete_video():
        """Handle video file deletion."""
        try:
            video_path = request.form.get('path')
            if not video_path:
                return jsonify({'error': 'No file path provided'}), 400

            # Handle YouTube videos - remove from library and delete downloaded files
            if video_path.startswith('youtube://'):
                # Get video entry first to check for downloaded file and thumbnail
                video_entry = video_player.library_manager.get_video(video_path)
                downloaded_file_deleted = False
                thumbnail_deleted = False

                if video_entry:
                    # Delete downloaded file if it exists
                    if video_entry.download_path and os.path.exists(video_entry.download_path):
                        try:
                            os.remove(video_entry.download_path)
                            downloaded_file_deleted = True
                            logger.info('Deleted downloaded file: %s', video_entry.download_path)
                        except OSError as e:
                            logger.error('Failed to delete downloaded file %s: %s', video_entry.download_path, e)
                    
                    # Delete thumbnail if it exists
                    if video_entry.thumbnail_path and os.path.exists(video_entry.thumbnail_path):
                        try:
                            os.remove(video_entry.thumbnail_path)
                            thumbnail_deleted = True
                            logger.info('Deleted thumbnail: %s', video_entry.thumbnail_path)
                        except OSError as e:
                            logger.error('Failed to delete thumbnail %s: %s', video_entry.thumbnail_path, e)

                # Remove from library database
                success = video_player.library_manager.remove_video(video_path)
                if success:
                    message = 'YouTube video removed from library'
                    if downloaded_file_deleted:
                        message += ' and downloaded file deleted'
                    if thumbnail_deleted:
                        message += ' and thumbnail deleted'
                    return jsonify({'success': message}), 200
                else:
                    return jsonify({'error': 'Failed to remove YouTube video'}), 500

            # Validate regular file path
            if not validator.validate_file_path(video_path, video_player.video_dirs):
                return jsonify({'error': 'Invalid file path'}), 400

            if not os.path.exists(video_path):
                return jsonify({'error': 'File not found'}), 404

            # Get video entry to check for thumbnail before deleting
            video_entry = video_player.library_manager.get_video(video_path)
            thumbnail_deleted = False
            
            if video_entry and video_entry.thumbnail_path and os.path.exists(video_entry.thumbnail_path):
                try:
                    os.remove(video_entry.thumbnail_path)
                    thumbnail_deleted = True
                    logger.info('Deleted thumbnail: %s', video_entry.thumbnail_path)
                except OSError as e:
                    logger.error('Failed to delete thumbnail %s: %s', video_entry.thumbnail_path, e)

            # Delete file
            os.remove(video_path)

            filename = os.path.basename(video_path)
            logger.info('Video deleted: %s', filename)
            
            message = f'Deleted {filename}'
            if thumbnail_deleted:
                message += ' and thumbnail'

            return jsonify({'success': message}), 200

        except OSError as e:
            logger.error('Delete error: %s', e)
            return jsonify({'error': 'Delete failed'}), 500

    @video_bp.route('/delete-offline', methods=['POST'])
    def delete_offline():
        """Delete the downloaded file for a YouTube video (keep the library entry)."""
        try:
            data = request.get_json()
            video_path = data.get('path')
            
            if not video_path:
                return jsonify({'error': 'No path provided'}), 400

            # Only works for YouTube videos
            if not video_path.startswith('youtube://'):
                return jsonify({'error': 'This endpoint only works for YouTube videos'}), 400

            # Get video entry to find download path
            video_entry = video_player.library_manager.get_video(video_path)
            
            if not video_entry:
                return jsonify({'error': 'Video not found'}), 404

            if not video_entry.download_path:
                return jsonify({'error': 'No downloaded file found'}), 404

            # Delete the downloaded file
            if os.path.exists(video_entry.download_path):
                try:
                    os.remove(video_entry.download_path)
                    logger.info('Deleted offline file: %s', video_entry.download_path)
                except OSError as e:
                    logger.error('Failed to delete offline file %s: %s', video_entry.download_path, e)
                    return jsonify({'error': 'Failed to delete file'}), 500

            # Update the database to remove download_path
            video_entry.download_path = None
            if video_player.library_manager.add_or_update_video(video_entry):
                return jsonify({'success': 'Offline file deleted'}), 200
            else:
                return jsonify({'error': 'Failed to update database'}), 500

        except (ValueError, KeyError) as e:
            logger.error('Delete offline error: %s', e)
            return jsonify({'error': 'Invalid request'}), 400

    @video_bp.route('/update', methods=['POST'])
    def update_video():
        """Handle video metadata update."""
        try:
            video_path = request.form.get('path')
            title = request.form.get('title', '').strip()
            custom_start_time = request.form.get('custom_start_time')
            custom_end_offset = request.form.get('custom_end_offset')

            if not video_path:
                return jsonify({'error': 'No file path provided'}), 400

            # Handle YouTube videos differently from regular files
            is_youtube = video_path.startswith('youtube://')

            if is_youtube:
                # For YouTube videos, just validate the format
                if not video_path.startswith('youtube://') or len(video_path.split('://')) != 2:
                    return jsonify({'error': 'Invalid YouTube video path'}), 400
            else:
                # Validate regular file path
                if not validator.validate_file_path(video_path, video_player.video_dirs):
                    return jsonify({'error': 'Invalid file path'}), 400

                if not os.path.exists(video_path):
                    return jsonify({'error': 'File not found'}), 404

            # Get video entry to access duration
            video_entry = video_player.get_video_entry(video_path)
            if not video_entry or not video_entry.duration:
                return jsonify({'error': 'Could not get video duration'}), 400

            # Parse and validate times
            start_time = None
            end_time = None

            if custom_start_time:
                try:
                    start_time = float(custom_start_time)
                    if start_time < 0:
                        return jsonify({'error': 'Start time cannot be negative'}), 400
                    if start_time >= video_entry.duration:
                        return jsonify({'error': 'Start time cannot be greater than video duration'}), 400
                except ValueError:
                    return jsonify({'error': 'Invalid start time format'}), 400

            if custom_end_offset:
                try:
                    end_offset = float(custom_end_offset)
                    if end_offset <= 0:
                        return jsonify({'error': 'End offset must be positive'}), 400
                    if end_offset >= video_entry.duration:
                        return jsonify({'error': 'End offset cannot be greater than video duration'}), 400

                    # Convert offset to absolute end time
                    end_time = video_entry.duration - end_offset

                    if start_time is not None and end_time <= start_time:
                        return jsonify({'error': 'End time must be after start time'}), 400
                except ValueError:
                    return jsonify({'error': 'Invalid end offset format'}), 400

            # Update video metadata
            success = video_player.update_video_metadata(
                video_path, title if title else None, start_time, end_time
            )

            if success:
                filename = os.path.basename(video_path)
                logger.info('Video metadata updated: %s', filename)
                return jsonify({'success': True, 'message': f'Updated {filename}'}), 200
            else:
                return jsonify({'error': 'Failed to update video metadata'}), 500

        except Exception as e:
            logger.error('Video update error: %s', e)
            return jsonify({'error': 'Update failed'}), 500

    return video_bp
