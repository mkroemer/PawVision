"""Statistics and analytics routes."""

import logging
import os
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')
logger = logging.getLogger(__name__)


def init_statistics_routes(app_context):
    """Initialize statistics routes with app context."""
    statistics_manager = app_context.get('statistics_manager')
    video_player = app_context['video_player']
    gpio_manager = app_context.get('gpio_manager')
    app = app_context.get('app')

    @statistics_bp.route('/')
    def get_statistics():
        """Get detailed statistics."""
        try:
            if not statistics_manager:
                return jsonify({'status': 'error', 'message': 'Statistics not enabled'}), 404

            stats = statistics_manager.get_summary()

            # Check if motion sensor/GPIO is enabled
            motion_sensor_enabled = gpio_manager is not None

            # Calculate average watch time from button press events
            avg_watch_time_str = '0m'
            if motion_sensor_enabled and 'button_presses' in stats:
                avg_watch_time = statistics_manager.get_average_watch_time()
                if avg_watch_time > 0:
                    if avg_watch_time >= 60:
                        minutes = int(avg_watch_time // 60)
                        seconds = int(avg_watch_time % 60)
                        avg_watch_time_str = f'{minutes}m {seconds}s' if seconds > 0 else f'{minutes}m'
                    else:
                        avg_watch_time_str = f'{int(avg_watch_time)}s'

            frontend_response = {
                'status': 'success',
                'stats': {
                    'total_plays': (
                        stats.get('button_presses', {}).get('total', 0)
                        if motion_sensor_enabled
                        else stats.get('video_plays', {}).get('total', 0)
                    ),
                    'total_watch_time_str': f"{stats.get('video_viewing', {}).get('total_duration', 0)/60:.0f}m",
                    'avg_daily_plays': (
                        stats.get('button_presses', {}).get('daily_average', 0) if motion_sensor_enabled else 0
                    ),
                    'motion_sensor_enabled': motion_sensor_enabled,
                    'avg_watch_time_str': avg_watch_time_str,
                    'plays_trend': 0,
                    'duration_trend': 0,
                },
                'charts': {
                    'plays': {
                        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        'data': [5, 8, 3, 12, 7, 4, 9],
                    }
                },
                'activity': [],
            }

            return jsonify(frontend_response), 200

        except Exception as e:
            logger.error('API statistics error: %s', e)
            return jsonify({'status': 'error', 'message': 'Internal error'}), 500

    @statistics_bp.route('/hourly')
    def get_hourly_statistics():
        """Get hourly statistics for a specific date."""
        try:
            if not statistics_manager:
                return jsonify({'status': 'error', 'message': 'Statistics not enabled'}), 404

            date_str = request.args.get('date')  # Expected format: YYYY-MM-DD
            hourly_data = statistics_manager.get_hourly_data(date_str)

            return jsonify({
                'status': 'success',
                'date': date_str or 'today',
                'hourly_data': hourly_data,
            }), 200

        except Exception as e:
            logger.error('API hourly statistics error: %s', e)
            return jsonify({'status': 'error', 'message': 'Internal error'}), 500

    @statistics_bp.route('/clear', methods=['POST'])
    def clear_statistics():
        """Clear all statistics."""
        try:
            if not statistics_manager:
                return jsonify({'status': 'error', 'message': 'Statistics not enabled'}), 404

            statistics_manager.reset_stats()
            logger.info('Statistics cleared via web interface')

            return jsonify({'status': 'success', 'message': 'Statistics cleared'}), 200

        except Exception as e:
            logger.error('API clear statistics error: %s', e)
            return jsonify({'status': 'error', 'message': 'Internal error'}), 500

    @statistics_bp.route('/export')
    def export_statistics():
        """Export statistics data."""
        try:
            if not statistics_manager:
                return jsonify({'error': 'Statistics not enabled'}), 404

            format_type = request.args.get('format', 'json').lower()
            stats = statistics_manager.get_summary()

            if format_type == 'csv':
                # Create a simple CSV export
                csv_data = 'metric,value\n'
                for key, value in stats.items():
                    csv_data += f'{key},{value}\n'

                response = app.response_class(
                    csv_data,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=pawvision-stats.csv'},
                )
                return response
            else:
                # JSON export
                response = app.response_class(
                    jsonify(stats).data,
                    mimetype='application/json',
                    headers={'Content-Disposition': 'attachment; filename=pawvision-stats.json'},
                )
                return response

        except Exception as e:
            logger.error('API export statistics error: %s', e)
            return jsonify({'error': 'Internal error'}), 500

    @statistics_bp.route('/report')
    def generate_report():
        """Generate statistics report."""
        try:
            if not statistics_manager:
                return jsonify({'error': 'Statistics not enabled'}), 404

            stats = statistics_manager.get_summary()

            # Generate a simple HTML report
            report_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>PawVision Statistics Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>PawVision Statistics Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
            """

            for key, value in stats.items():
                report_html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"

            report_html += """
                </table>
            </body>
            </html>
            """

            response = app.response_class(
                report_html,
                mimetype='text/html',
                headers={'Content-Disposition': 'attachment; filename=pawvision-report.html'},
            )
            return response

        except Exception as e:
            logger.error('API generate report error: %s', e)
            return jsonify({'error': 'Internal error'}), 500

    @statistics_bp.route('/summary')
    def get_summary():
        """Get statistics summary for React frontend."""
        try:
            if not statistics_manager:
                return jsonify({'success': False, 'message': 'Statistics not enabled'}), 404

            # Get videos from database for total count
            videos = video_player.get_video_library_entries()
            total_videos = len(videos)

            # Query database for statistics
            conn = sqlite3.connect(statistics_manager.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Total plays
            cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_type = 'video' AND action = 'play'")
            total_plays = cursor.fetchone()['count']

            # Total duration
            cursor.execute("SELECT SUM(duration) as total FROM events WHERE event_type = 'video' AND duration IS NOT NULL")
            result = cursor.fetchone()
            total_duration = result['total'] or 0

            # Favorite video
            cursor.execute("""
                SELECT video_file, COUNT(*) as play_count
                FROM events
                WHERE event_type = 'video' AND action = 'play' AND video_file IS NOT NULL
                GROUP BY video_file
                ORDER BY play_count DESC
                LIMIT 1
            """)
            fav_row = cursor.fetchone()
            favorite_video = None
            if fav_row and fav_row['video_file']:
                favorite_video = {
                    'title': os.path.basename(fav_row['video_file']),
                    'play_count': fav_row['play_count']
                }

            # Recent plays
            cursor.execute("""
                SELECT video_file, timestamp, duration
                FROM events
                WHERE event_type = 'video' AND action = 'play' AND video_file IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent_rows = cursor.fetchall()
            recent_plays = [
                {
                    'video_title': os.path.basename(row['video_file']),
                    'timestamp': row['timestamp'],
                    'duration': row['duration'] or 0
                }
                for row in recent_rows
            ]

            conn.close()

            return jsonify({
                'success': True,
                'data': {
                    'total_plays': total_plays,
                    'total_duration': total_duration,
                    'total_videos': total_videos,
                    'favorite_video': favorite_video,
                    'recent_plays': recent_plays
                }
            }), 200

        except Exception as e:
            logger.error('API statistics summary error: %s', e)
            return jsonify({'success': False, 'message': 'Internal error'}), 500

    @statistics_bp.route('/plays-by-day')
    def get_plays_by_day():
        """Get plays by day for chart."""
        try:
            if not statistics_manager:
                return jsonify({'success': False, 'message': 'Statistics not enabled'}), 404

            days = request.args.get('days', 30, type=int)

            conn = sqlite3.connect(statistics_manager.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get plays grouped by day
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as plays
                FROM events
                WHERE event_type = 'video'
                  AND action = 'play'
                  AND timestamp >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """, (days,))

            rows = cursor.fetchall()
            plays_by_day = [
                {
                    'date': row['date'],
                    'plays': row['plays']
                }
                for row in rows
            ]

            conn.close()

            return jsonify({
                'success': True,
                'data': plays_by_day
            }), 200

        except Exception as e:
            logger.error('API plays by day error: %s', e)
            return jsonify({'success': False, 'message': 'Internal error'}), 500

    @statistics_bp.route('/plays-by-video')
    def get_plays_by_video():
        """Get plays by video for chart."""
        try:
            if not statistics_manager:
                return jsonify({'success': False, 'message': 'Statistics not enabled'}), 404

            limit = request.args.get('limit', 10, type=int)

            conn = sqlite3.connect(statistics_manager.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get plays grouped by video
            cursor.execute("""
                SELECT
                    video_file,
                    COUNT(*) as play_count,
                    SUM(duration) as total_duration
                FROM events
                WHERE event_type = 'video'
                  AND action = 'play'
                  AND video_file IS NOT NULL
                GROUP BY video_file
                ORDER BY play_count DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            plays_by_video = [
                {
                    'video_title': os.path.basename(row['video_file']),
                    'play_count': row['play_count'],
                    'total_duration': row['total_duration'] or 0
                }
                for row in rows
            ]

            conn.close()

            return jsonify({
                'success': True,
                'data': plays_by_video
            }), 200

        except Exception as e:
            logger.error('API plays by video error: %s', e)
            return jsonify({'success': False, 'message': 'Internal error'}), 500

    return statistics_bp
