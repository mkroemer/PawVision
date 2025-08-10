"""Statistics tracking for PawVision using unified SQLite database."""

import logging
import os
from datetime import datetime
from typing import Dict
from threading import Lock
from .database import PawVisionDatabase


class StatisticsManager:
    """Manages PawVision usage statistics with unified SQLite backend."""
    
    def __init__(self, db_path: str, enabled: bool = True, cooldown_seconds: int = 60,
                 legacy_json_file: str = None):
        self.db = PawVisionDatabase(db_path)
        self.enabled = enabled
        self.cooldown_seconds = cooldown_seconds
        self.last_button_press = None
        self.stats_lock = Lock()
        self.logger = logging.getLogger(__name__)
        
        if self.enabled:
            # Migrate from legacy JSON file if it exists
            if legacy_json_file and os.path.exists(legacy_json_file):
                self.db.migrate_json_statistics(legacy_json_file)
            
            self._load_last_button_press()
            self.logger.info("Statistics manager initialized with unified database")
        else:
            self.logger.info("Statistics disabled")
    
    def _load_last_button_press(self):
        """Load the timestamp of the last button press from database."""
        if not self.enabled:
            return
        
        try:
            # Get the last button press event from the events table
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                result = conn.execute(
                    "SELECT timestamp FROM events WHERE event_type = 'button_press' ORDER BY timestamp DESC LIMIT 1"
                ).fetchone()
                
                if result:
                    # Parse the timestamp (SQLite stores as string)
                    timestamp_str = result[0]
                    if 'T' in timestamp_str:
                        self.last_button_press = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        self.last_button_press = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    self.logger.debug("Last button press loaded: %s", self.last_button_press)
                
        except (ValueError, TypeError, OSError) as e:
            self.logger.error("Error loading last button press: %s", e)
    
    def _is_button_press_allowed(self) -> bool:
        """Check if button press is allowed based on cooldown period."""
        if not self.last_button_press:
            return True
        
        now = datetime.now()
        time_since_last = (now - self.last_button_press).total_seconds()
        
        if time_since_last < self.cooldown_seconds:
            remaining_cooldown = self.cooldown_seconds - time_since_last
            self.logger.info("Button press blocked by cooldown. %d seconds remaining", remaining_cooldown)
            return False
        
        return True
    
    def set_cooldown_period(self, seconds: int):
        """Update the cooldown period."""
        self.cooldown_seconds = max(0, seconds)
        self.logger.info("Button cooldown period set to %d seconds", self.cooldown_seconds)
    
    def record_button_press(self, action: str = "play", duration: float = None, 
                           video_file: str = None, force: bool = False, is_interruption: bool = False):
        """Record a button press event with cooldown protection.
        
        Args:
            action: The action performed ('play' or 'stop')
            duration: Duration of button press in seconds
            video_file: Video file associated with the action
            force: If True, bypass cooldown protection (for API/web calls)
            is_interruption: If True, this was a button press during playback (stop action)
        
        Returns:
            bool: True if button press was recorded, False if blocked by cooldown
        """
        if not self.enabled:
            return True
        
        # Check cooldown period (unless forced)
        if not force and not self._is_button_press_allowed():
            return False
        
        # Update last button press time
        self.last_button_press = datetime.now()
        
        # Log detailed event to database
        self.db.log_event(
            event_type='button_press' if not is_interruption else 'button_interruption',
            action=action,
            details={'duration': duration, 'is_interruption': is_interruption},
            video_file=video_file,
            duration=duration,
            source='button'
        )
        
        # Update aggregated statistics
        self._update_button_statistics(action, is_interruption)
        
        self.logger.info("Button press recorded: %s (interruption: %s)", action, is_interruption)
        return True
    
    def _update_button_statistics(self, action: str, is_interruption: bool):
        """Update aggregated button press statistics."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            hour = datetime.now().hour
            
            # Update totals
            total = self.db.get_statistic('button_presses', 'total', default=0)
            self.db.set_statistic('button_presses', 'total', total + 1)
            
            # Update action counts
            if action == 'play':
                play_count = self.db.get_statistic('button_presses', 'play_actions', default=0)
                self.db.set_statistic('button_presses', 'play_actions', play_count + 1)
            elif action == 'stop':
                stop_count = self.db.get_statistic('button_presses', 'stop_actions', default=0)
                self.db.set_statistic('button_presses', 'stop_actions', stop_count + 1)
            
            # Update daily statistics
            daily_stats = self.db.get_statistic('button_presses', 'daily', default={})
            daily_stats[today] = daily_stats.get(today, 0) + 1
            self.db.set_statistic('button_presses', 'daily', daily_stats)
            
            # Update hourly statistics
            hourly_stats = self.db.get_statistic('button_presses', 'hourly', default={})
            hourly_stats[str(hour)] = hourly_stats.get(str(hour), 0) + 1
            self.db.set_statistic('button_presses', 'hourly', hourly_stats)
            
            # Update interruption count if applicable
            if is_interruption:
                interruptions = self.db.get_statistic('interruptions', 'total', default=0)
                self.db.set_statistic('interruptions', 'total', interruptions + 1)
                
                daily_interruptions = self.db.get_statistic('interruptions', 'daily', default={})
                daily_interruptions[today] = daily_interruptions.get(today, 0) + 1
                self.db.set_statistic('interruptions', 'daily', daily_interruptions)
            
        except (ValueError, TypeError) as e:
            self.logger.error("Error updating button statistics: %s", e)
    
    def record_video_play(self, video_file: str, trigger: str = "button"):
        """Record when a video starts playing."""
        if not self.enabled:
            return
        
        self.db.log_event(
            event_type='video_play',
            action='start',
            details={'trigger': trigger},
            video_file=video_file,
            source=trigger
        )
        
        self._update_video_play_statistics(video_file, trigger)
        
        self.logger.debug("Video play recorded: %s (trigger: %s)", os.path.basename(video_file), trigger)
    
    def _update_video_play_statistics(self, video_file: str, trigger: str):
        """Update aggregated video play statistics."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            hour = datetime.now().hour
            filename = os.path.basename(video_file)
            
            # Update totals
            total = self.db.get_statistic('video_plays', 'total', default=0)
            self.db.set_statistic('video_plays', 'total', total + 1)
            
            # Update by video statistics
            by_video = self.db.get_statistic('video_plays', 'by_video', default={})
            by_video[filename] = by_video.get(filename, 0) + 1
            self.db.set_statistic('video_plays', 'by_video', by_video)
            
            # Update daily statistics
            daily_stats = self.db.get_statistic('video_plays', 'daily', default={})
            daily_stats[today] = daily_stats.get(today, 0) + 1
            self.db.set_statistic('video_plays', 'daily', daily_stats)
            
            # Update hourly statistics
            hourly_stats = self.db.get_statistic('video_plays', 'hourly', default={})
            hourly_stats[str(hour)] = hourly_stats.get(str(hour), 0) + 1
            self.db.set_statistic('video_plays', 'hourly', hourly_stats)
            
            # Update scheduled play statistics if applicable
            if trigger == 'scheduled':
                scheduled_total = self.db.get_statistic('scheduled_plays', 'total', default=0)
                self.db.set_statistic('scheduled_plays', 'total', scheduled_total + 1)
                
                scheduled_daily = self.db.get_statistic('scheduled_plays', 'daily', default={})
                scheduled_daily[today] = scheduled_daily.get(today, 0) + 1
                self.db.set_statistic('scheduled_plays', 'daily', scheduled_daily)
            
        except (ValueError, TypeError) as e:
            self.logger.error("Error updating video play statistics: %s", e)
    
    def record_video_viewing(self, video_file: str, duration: float, end_reason: str = "timeout"):
        """Record video viewing session details."""
        if not self.enabled:
            return
        
        self.db.log_event(
            event_type='video_viewing',
            action='complete',
            details={'end_reason': end_reason},
            video_file=video_file,
            duration=duration,
            source='player'
        )
        
        self._update_viewing_statistics(video_file, duration, end_reason)
        
        self.logger.debug("Video viewing recorded: %s (%.1fs, %s)", 
                         os.path.basename(video_file), duration, end_reason)
    
    def _update_viewing_statistics(self, video_file: str, duration: float, end_reason: str):
        """Update aggregated viewing statistics."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            filename = os.path.basename(video_file)
            
            # Update session count
            sessions = self.db.get_statistic('video_viewing', 'total_sessions', default=0)
            self.db.set_statistic('video_viewing', 'total_sessions', sessions + 1)
            
            # Update total duration
            total_duration = self.db.get_statistic('video_viewing', 'total_duration', default=0.0)
            new_total = total_duration + duration
            self.db.set_statistic('video_viewing', 'total_duration', new_total)
            
            # Update average duration
            avg_duration = new_total / (sessions + 1)
            self.db.set_statistic('video_viewing', 'average_duration', avg_duration)
            
            # Update by end reason
            by_reason = self.db.get_statistic('video_viewing', 'by_end_reason', default={})
            by_reason[end_reason] = by_reason.get(end_reason, 0) + 1
            self.db.set_statistic('video_viewing', 'by_end_reason', by_reason)
            
            # Update by video
            by_video = self.db.get_statistic('video_viewing', 'by_video', default={})
            if filename not in by_video:
                by_video[filename] = {'sessions': 0, 'total_duration': 0.0}
            by_video[filename]['sessions'] += 1
            by_video[filename]['total_duration'] += duration
            self.db.set_statistic('video_viewing', 'by_video', by_video)
            
            # Update daily statistics
            daily_stats = self.db.get_statistic('video_viewing', 'daily', default={})
            if today not in daily_stats:
                daily_stats[today] = {'sessions': 0, 'duration': 0.0}
            daily_stats[today]['sessions'] += 1
            daily_stats[today]['duration'] += duration
            self.db.set_statistic('video_viewing', 'daily', daily_stats)
            
        except (ValueError, TypeError) as e:
            self.logger.error("Error updating viewing statistics: %s", e)
    
    def record_api_call(self, action: str):
        """Record API call for statistics."""
        if not self.enabled:
            return
        
        self.db.log_event(
            event_type='api_call',
            action=action,
            source='api'
        )
        
        self._update_api_statistics(action)
    
    def _update_api_statistics(self, action: str):
        """Update aggregated API call statistics."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Update totals
            total = self.db.get_statistic('api_calls', 'total', default=0)
            self.db.set_statistic('api_calls', 'total', total + 1)
            
            # Update action-specific counts
            action_count = self.db.get_statistic('api_calls', action, default=0)
            self.db.set_statistic('api_calls', action, action_count + 1)
            
            # Update daily statistics
            daily_stats = self.db.get_statistic('api_calls', 'daily', default={})
            daily_stats[today] = daily_stats.get(today, 0) + 1
            self.db.set_statistic('api_calls', 'daily', daily_stats)
            
        except (ValueError, TypeError) as e:
            self.logger.error("Error updating API statistics: %s", e)
    
    def get_summary(self) -> Dict:
        """Get a summary of all statistics."""
        if not self.enabled:
            return {}
        
        try:
            summary = {}
            
            # Get all statistics categories
            categories = ['button_presses', 'video_plays', 'video_viewing', 'scheduled_plays', 'api_calls', 'interruptions']
            
            for category in categories:
                summary[category] = self.db.get_statistics_by_category(category)
            
            # Add system information
            summary['system'] = {
                'last_updated': datetime.now().isoformat(),
                'database_path': self.db.db_path
            }
            
            return summary
            
        except (ValueError, TypeError, OSError) as e:
            self.logger.error("Error getting statistics summary: %s", e)
            return {}
    
    def clear_all_statistics(self) -> bool:
        """Clear all statistics data."""
        if not self.enabled:
            return True
        
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                # Clear events table
                conn.execute("DELETE FROM events")
                # Clear statistics summary table
                conn.execute("DELETE FROM statistics_summary")
                conn.commit()
            
            # Reset last button press
            self.last_button_press = None
            
            self.logger.info("All statistics cleared")
            return True
            
        except (OSError, ValueError) as e:
            self.logger.error("Error clearing statistics: %s", e)
            return False
    
    def get_viewing_time_by_date(self, date: str) -> float:
        """Get total viewing time for a specific date."""
        try:
            daily_stats = self.db.get_statistic('video_viewing', 'daily', default={})
            return daily_stats.get(date, {}).get('duration', 0.0)
        except (ValueError, TypeError) as e:
            self.logger.error("Error getting viewing time for date %s: %s", date, e)
            return 0.0
    
    def get_button_presses_by_date(self, date: str) -> int:
        """Get total button presses for a specific date."""
        try:
            daily_stats = self.db.get_statistic('button_presses', 'daily', default={})
            return daily_stats.get(date, 0)
        except (ValueError, TypeError) as e:
            self.logger.error("Error getting button presses for date %s: %s", date, e)
            return 0
