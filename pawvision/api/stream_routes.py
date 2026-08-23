"""Stream routes for mirroring HDMI playback to web."""

import logging
import os
from flask import Blueprint, Response, jsonify, request

stream_bp = Blueprint('stream', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


def init_stream_routes(app_context):
    """Initialize stream routes with app context."""
    global stream_bp
    stream_bp = Blueprint('stream', __name__, url_prefix='/api')
    video_player = app_context['video_player']
    statistics_manager = app_context.get('statistics_manager')

    @stream_bp.route('/stream/current')
    def stream_current_video():
        """Stream the video that's currently playing on HDMI.
        
        Returns:
            - Video stream if a video is playing
            - JSON error if no video is playing
            - 416 Range Not Satisfiable if range request is invalid
        """
        try:
            # Get current video info
            video_info = video_player.get_current_video_info()
            
            if not video_info:
                return jsonify({
                    'error': 'No video currently playing',
                    'playing': False
                }), 404

            video_path = video_info['path']
            
            # Handle YouTube videos
            if video_info['is_youtube']:
                # Get the video entry to access stream URL
                video_entry = video_player.get_video_entry(video_path)
                if video_entry and video_entry.download_path and os.path.exists(video_entry.download_path):
                    # Use downloaded file if available
                    video_path = video_entry.download_path
                elif video_entry and video_entry.stream_url:
                    # Return redirect to stream URL
                    return jsonify({
                        'stream_url': video_entry.stream_url,
                        'video_info': video_info,
                        'redirect': True
                    }), 200
                else:
                    return jsonify({
                        'error': 'YouTube video stream not available',
                        'playing': True
                    }), 503

            # Check if file exists
            if not os.path.exists(video_path):
                return jsonify({
                    'error': 'Video file not found',
                    'path': video_path,
                    'playing': True
                }), 404

            # Get file info
            file_size = os.path.getsize(video_path)
            
            # Handle range requests for video seeking
            range_header = request.headers.get('Range')
            
            if range_header:
                # Parse range header
                byte_range = range_header.strip().replace('bytes=', '').split('-')
                start = int(byte_range[0]) if byte_range[0] else 0
                end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
                
                # Validate range
                if start >= file_size or end >= file_size or start > end:
                    return Response(status=416)
                
                length = end - start + 1
                
                # Stream the requested range
                def generate_chunk():
                    with open(video_path, 'rb') as f:
                        f.seek(start)
                        remaining = length
                        chunk_size = 8192  # 8KB chunks
                        
                        while remaining > 0:
                            read_size = min(chunk_size, remaining)
                            data = f.read(read_size)
                            if not data:
                                break
                            remaining -= len(data)
                            yield data
                
                # Determine content type
                content_type = _get_content_type(video_path)
                
                response = Response(
                    generate_chunk(),
                    206,  # Partial Content
                    mimetype=content_type,
                    direct_passthrough=True
                )
                response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
                response.headers.add('Accept-Ranges', 'bytes')
                response.headers.add('Content-Length', str(length))
                
                if statistics_manager:
                    statistics_manager.record_api_call('stream_current')
                
                return response
            
            else:
                # No range request, stream entire file
                def generate_full():
                    with open(video_path, 'rb') as f:
                        chunk_size = 8192  # 8KB chunks
                        while True:
                            data = f.read(chunk_size)
                            if not data:
                                break
                            yield data
                
                content_type = _get_content_type(video_path)
                
                response = Response(
                    generate_full(),
                    200,
                    mimetype=content_type,
                    direct_passthrough=True
                )
                response.headers.add('Content-Length', str(file_size))
                response.headers.add('Accept-Ranges', 'bytes')
                
                if statistics_manager:
                    statistics_manager.record_api_call('stream_current')
                
                return response

        except (OSError, IOError, ValueError) as e:
            logger.error('Stream current video error: %s', e, exc_info=True)
            return jsonify({
                'error': 'Failed to stream video',
                'details': str(e)
            }), 500

    @stream_bp.route('/stream/info')
    def stream_info():
        """Get information about the currently streaming video.
        
        Returns video metadata without streaming the actual content.
        """
        try:
            video_info = video_player.get_current_video_info()
            
            if not video_info:
                return jsonify({
                    'playing': False,
                    'video': None
                }), 200

            # Add streaming availability info
            video_path = video_info['path']
            streamable = False
            stream_type = None
            
            if video_info['is_youtube']:
                video_entry = video_player.get_video_entry(video_path)
                if video_entry:
                    if video_entry.download_path and os.path.exists(video_entry.download_path):
                        streamable = True
                        stream_type = 'local'
                    elif video_entry.stream_url:
                        streamable = True
                        stream_type = 'redirect'
            else:
                streamable = os.path.exists(video_path)
                stream_type = 'local' if streamable else None

            return jsonify({
                'playing': True,
                'video': video_info,
                'streamable': streamable,
                'stream_type': stream_type
            }), 200

        except (OSError, IOError, ValueError, AttributeError) as e:
            logger.error('Stream info error: %s', e)
            return jsonify({
                'error': 'Failed to get stream info',
                'details': str(e)
            }), 500

    return stream_bp


def _get_content_type(video_path: str) -> str:
    """Get the MIME type for a video file based on extension."""
    ext = os.path.splitext(video_path)[1].lower()
    
    content_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.flv': 'video/x-flv',
        '.wmv': 'video/x-ms-wmv',
        '.m4v': 'video/x-m4v',
        '.ts': 'video/mp2t',
        '.3gp': 'video/3gpp',
        '.ogv': 'video/ogg',
    }
    
    return content_types.get(ext, 'video/mp4')  # Default to mp4
