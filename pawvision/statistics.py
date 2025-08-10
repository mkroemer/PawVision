"""Statistics tracking for PawVision using SQLite for detailed event logging."""

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict
from threading import Lock


class StatisticsManager:
    """Manages PawVision usage statistics with SQLite backend."""
    
    def __init__(self, stats_file: str, db_file: str, enabled: bool = True, cooldown_seconds: int = 60):
        self.stats_file = stats_file
        self.db_file = db_file
        self.enabled = enabled
        self.cooldown_seconds = cooldown_seconds
        self.last_button_press = None
        self.stats_lock = Lock()
        self.logger = logging.getLogger(__name__)
        
        if self.enabled:
            self._init_database()
            self._stats = self._load_stats()
            self._load_last_button_press()
        else:
            self._stats = {}
    
    def _init_database(self):
        """Initialize SQLite database with required schema."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            
            with sqlite3.connect(self.db_file) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT NOT NULL,
                        action TEXT,
                        details TEXT,
                        video_file TEXT,
                        duration REAL,
                        source TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_action ON events(action)')
                
                conn.commit()
                
            self.logger.info("Statistics database initialized: %s", self.db_file)
            
        except sqlite3.Error as e:
            self.logger.error("Failed to initialize statistics database: %s", e)
            self.enabled = False
    
    def _log_event(self, event_type: str, action: str = None, details: Dict = None, 
                   video_file: str = None, duration: float = None, source: str = 'system'):
        """Log an event to SQLite database."""
        if not self.enabled:
            return
        
        try:
            details_json = json.dumps(details) if details else None
            
            with sqlite3.connect(self.db_file) as conn:
                conn.execute('''
                    INSERT INTO events (event_type, action, details, video_file, duration, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (event_type, action, details_json, video_file, duration, source))
                conn.commit()
                
            self.logger.debug("Event logged: %s - %s", event_type, action)
            
        except sqlite3.Error as e:
            self.logger.error("Failed to log event: %s", e)
    
    def _load_last_button_press(self):
        """Load the timestamp of the last button press from database."""
        if not self.enabled:
            return
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                result = conn.execute(
                    "SELECT timestamp FROM events WHERE event_type = 'button_press' ORDER BY timestamp DESC LIMIT 1"
                ).fetchone()
                
                if result:
                    self.last_button_press = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                    self.logger.debug("Last button press loaded: %s", self.last_button_press)
                
        except sqlite3.Error as e:
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
    
    def _load_stats(self) -> Dict:
        """Load aggregated statistics from JSON file."""
        default_stats = {
            "button_presses": {
                "total": 0,
                "play_actions": 0,
                "stop_actions": 0,
                "daily": {},
                "hourly": {}
            },
            "video_plays": {
                "total": 0,
                "by_video": {},
                "daily": {},
                "hourly": {}
            },
            "video_viewing": {
                "total_sessions": 0,
                "total_duration": 0.0,
                "average_duration": 0.0,
                "by_end_reason": {},
                "by_video": {},
                "daily": {},
                "hourly": {}
            },
            "scheduled_plays": {
                "total": 0,
                "by_time": {},
                "daily": {}
            },
            "api_calls": {
                "total": 0,
                "play": 0,
                "stop": 0,
                "daily": {}
            },
            "interruptions": {
                "total": 0,
                "by_video": {},
                "daily": {},
                "hourly": {}
            },
            "system": {
                "last_updated": None,
                "start_time": datetime.now().isoformat(),
                "total_uptime_hours": 0
            }
        }
        
        if not self.enabled:
            return default_stats
        
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                for key, value in default_stats.items():
                    if key not in stats:
                        stats[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in stats[key]:
                                stats[key][subkey] = subvalue
                
                self.logger.info("Statistics loaded from %s", self.stats_file)
                return stats
            else:
                self.logger.info("Statistics file not found, creating new: %s", self.stats_file)
                self._save_stats_to_file(default_stats)
                return default_stats
        
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error("Error loading statistics: %s", e)
            self.logger.info("Using default statistics")
            return default_stats
    
    def _save_stats_to_file(self, stats: Dict = None):
        """Save aggregated statistics to JSON file."""
        if not self.enabled:
            return
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            
            with self.stats_lock:
                stats_to_save = stats or self._stats
                stats_to_save["system"]["last_updated"] = datetime.now().isoformat()
                
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(stats_to_save, f, indent=2)
            
            self.logger.debug("Statistics saved to %s", self.stats_file)
        
        except OSError as e:
            self.logger.error("Failed to save statistics: %s", e)
    
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
        
        # Log detailed event to SQLite
        self._log_event(
            event_type='button_press' if not is_interruption else 'button_interruption',
            action=action,
            details={
                'button_duration': duration, 
                'cooldown_bypassed': force,
                'is_interruption': is_interruption
            },
            video_file=video_file,
            duration=duration,
            source='physical_button' if not force else 'web_api'
        )
        
        # Update aggregated stats
        with self.stats_lock:
            if is_interruption:
                # Track interruptions separately
                if "interruptions" not in self._stats:
                    self._stats["interruptions"] = {
                        "total": 0,
                        "by_video": {},
                        "daily": {},
                        "hourly": {}
                    }
                
                self._stats["interruptions"]["total"] += 1
                
                # Track which videos get interrupted most
                if video_file:
                    self._stats["interruptions"]["by_video"][video_file] = \
                        self._stats["interruptions"]["by_video"].get(video_file, 0) + 1
                
                # Update daily and hourly interruption stats
                today = datetime.now().strftime("%Y-%m-%d")
                hour = datetime.now().strftime("%Y-%m-%d-%H")
                
                self._stats["interruptions"]["daily"][today] = \
                    self._stats["interruptions"]["daily"].get(today, 0) + 1
                self._stats["interruptions"]["hourly"][hour] = \
                    self._stats["interruptions"]["hourly"].get(hour, 0) + 1
            else:
                # Normal button press stats (only for play actions or forced stops)
                self._stats["button_presses"]["total"] += 1
                if action == "play":
                    self._stats["button_presses"]["play_actions"] += 1
                elif action == "stop":
                    self._stats["button_presses"]["stop_actions"] += 1
                
                # Update daily and hourly stats
                today = datetime.now().strftime("%Y-%m-%d")
                hour = datetime.now().strftime("%Y-%m-%d-%H")
                
                if today not in self._stats["button_presses"]["daily"]:
                    self._stats["button_presses"]["daily"][today] = {}
                self._stats["button_presses"]["daily"][today][action] = \
                    self._stats["button_presses"]["daily"][today].get(action, 0) + 1
                
                if hour not in self._stats["button_presses"]["hourly"]:
                    self._stats["button_presses"]["hourly"][hour] = {}
                self._stats["button_presses"]["hourly"][hour][action] = \
                    self._stats["button_presses"]["hourly"][hour].get(action, 0) + 1
            hour = datetime.now().strftime("%Y-%m-%d-%H")
            
            if today not in self._stats["button_presses"]["daily"]:
                self._stats["button_presses"]["daily"][today] = {}
            self._stats["button_presses"]["daily"][today][action] = \
                self._stats["button_presses"]["daily"][today].get(action, 0) + 1
            
            if hour not in self._stats["button_presses"]["hourly"]:
                self._stats["button_presses"]["hourly"][hour] = {}
            self._stats["button_presses"]["hourly"][hour][action] = \
                self._stats["button_presses"]["hourly"][hour].get(action, 0) + 1
        
        self._save_stats_to_file()
        self.logger.info("Button press recorded: %s (cooldown: %ds)", action, self.cooldown_seconds)
        return True
    
    def record_video_play(self, video_file: str, source: str = "button", duration: float = None):
        """Record a video play event."""
        if not self.enabled:
            return
        
        # Log detailed event to SQLite
        self._log_event(
            event_type='video_play',
            action='start',
            details={'video_duration': duration},
            video_file=video_file,
            duration=duration,
            source=source
        )
        
        # Update aggregated stats
        with self.stats_lock:
            self._stats["video_plays"]["total"] += 1
            self._stats["video_plays"]["by_video"][video_file] = \
                self._stats["video_plays"]["by_video"].get(video_file, 0) + 1
            
            # Update daily and hourly stats
            today = datetime.now().strftime("%Y-%m-%d")
            hour = datetime.now().strftime("%Y-%m-%d-%H")
            
            self._stats["video_plays"]["daily"][today] = \
                self._stats["video_plays"]["daily"].get(today, 0) + 1
            self._stats["video_plays"]["hourly"][hour] = \
                self._stats["video_plays"]["hourly"].get(hour, 0) + 1
        
        self._save_stats_to_file()
        self.logger.info("Video play recorded: %s", video_file)
    
    def record_video_viewing(self, video_file: str, viewing_duration: float, end_reason: str = "manual"):
        """Record video viewing duration and end reason."""
        if not self.enabled:
            return
        
        # Log detailed event to SQLite
        self._log_event(
            event_type='video_viewing',
            action='end',
            details={
                'viewing_duration': viewing_duration,
                'end_reason': end_reason,  # "manual", "timeout", "motion_sensor"
                'duration_minutes': round(viewing_duration / 60, 2)
            },
            video_file=video_file
        )
        
        # Update aggregated stats
        with self.stats_lock:
            if "video_viewing" not in self._stats:
                self._stats["video_viewing"] = {
                    "total_sessions": 0,
                    "total_duration": 0.0,
                    "average_duration": 0.0,
                    "by_end_reason": {},
                    "by_video": {},
                    "daily": {},
                    "hourly": {}
                }
            
            viewing_stats = self._stats["video_viewing"]
            viewing_stats["total_sessions"] += 1
            viewing_stats["total_duration"] += viewing_duration
            viewing_stats["average_duration"] = viewing_stats["total_duration"] / viewing_stats["total_sessions"]
            
            # Track by end reason
            viewing_stats["by_end_reason"][end_reason] = \
                viewing_stats["by_end_reason"].get(end_reason, 0) + 1
            
            # Track by video
            if video_file not in viewing_stats["by_video"]:
                viewing_stats["by_video"][video_file] = {
                    "sessions": 0,
                    "total_duration": 0.0,
                    "average_duration": 0.0
                }
            
            video_viewing = viewing_stats["by_video"][video_file]
            video_viewing["sessions"] += 1
            video_viewing["total_duration"] += viewing_duration
            video_viewing["average_duration"] = video_viewing["total_duration"] / video_viewing["sessions"]
            
            # Update daily and hourly stats
            today = datetime.now().strftime("%Y-%m-%d")
            hour = datetime.now().strftime("%Y-%m-%d-%H")
            
            if today not in viewing_stats["daily"]:
                viewing_stats["daily"][today] = {"sessions": 0, "duration": 0.0}
            viewing_stats["daily"][today]["sessions"] += 1
            viewing_stats["daily"][today]["duration"] += viewing_duration
            
            if hour not in viewing_stats["hourly"]:
                viewing_stats["hourly"][hour] = {"sessions": 0, "duration": 0.0}
            viewing_stats["hourly"][hour]["sessions"] += 1
            viewing_stats["hourly"][hour]["duration"] += viewing_duration
        
        self._save_stats_to_file()
        self.logger.info("Video viewing recorded: %s (%.1fs, %s)", 
                        video_file, viewing_duration, end_reason)

    def record_scheduled_play(self, schedule_time: str, video_file: str):
        """Record a scheduled play event."""
        if not self.enabled:
            return
        
        # Log detailed event to SQLite
        self._log_event(
            event_type='scheduled_play',
            action='start',
            details={'schedule_time': schedule_time},
            video_file=video_file,
            source='scheduler'
        )
        
        # Update aggregated stats
        with self.stats_lock:
            self._stats["scheduled_plays"]["total"] += 1
            self._stats["scheduled_plays"]["by_time"][schedule_time] = \
                self._stats["scheduled_plays"]["by_time"].get(schedule_time, 0) + 1
            
            today = datetime.now().strftime("%Y-%m-%d")
            self._stats["scheduled_plays"]["daily"][today] = \
                self._stats["scheduled_plays"]["daily"].get(today, 0) + 1
        
        self._save_stats_to_file()
        self.logger.info("Scheduled play recorded: %s at %s", video_file, schedule_time)
    
    def record_api_call(self, endpoint: str, action: str = None):
        """Record an API call event."""
        if not self.enabled:
            return
        
        # Log detailed event to SQLite
        self._log_event(
            event_type='api_call',
            action=action or endpoint,
            details={'endpoint': endpoint},
            source='web_api'
        )
        
        # Update aggregated stats
        with self.stats_lock:
            self._stats["api_calls"]["total"] += 1
            if action:
                self._stats["api_calls"][action] = \
                    self._stats["api_calls"].get(action, 0) + 1
            
            today = datetime.now().strftime("%Y-%m-%d")
            self._stats["api_calls"]["daily"][today] = \
                self._stats["api_calls"]["daily"].get(today, 0) + 1
        
        self._save_stats_to_file()
        self.logger.debug("API call recorded: %s", endpoint)
    
    def get_stats(self) -> Dict:
        """Get current aggregated statistics."""
        with self.stats_lock:
            return self._stats.copy()
    
    def get_summary(self) -> Dict:
        """Get a summary of key statistics from SQLite and aggregated data."""
        if not self.enabled:
            return {}
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Get basic counts
                total_button_presses = conn.execute(
                    "SELECT COUNT(*) FROM events WHERE event_type = 'button_press'"
                ).fetchone()[0]
                
                # Get today's button presses
                today_button_presses = conn.execute(
                    "SELECT COUNT(*) FROM events WHERE event_type = 'button_press' AND date(timestamp) = date('now')"
                ).fetchone()[0]
                
                # Get total viewing duration (in minutes)
                total_viewing_result = conn.execute(
                    "SELECT COALESCE(SUM(duration), 0) FROM events WHERE event_type = 'video_viewing'"
                ).fetchone()
                total_viewing_minutes = round(total_viewing_result[0] / 60, 1) if total_viewing_result[0] else 0
                
                # Get yesterday's viewing duration
                yesterday_viewing_result = conn.execute(
                    "SELECT COALESCE(SUM(duration), 0) FROM events WHERE event_type = 'video_viewing' AND date(timestamp) = date('now', '-1 day')"
                ).fetchone()
                yesterday_viewing_minutes = round(yesterday_viewing_result[0] / 60, 1) if yesterday_viewing_result[0] else 0
                
                # Get recent activity (last 10 events)
                recent_events = conn.execute(
                    "SELECT event_type, action, video_file, timestamp FROM events ORDER BY timestamp DESC LIMIT 10"
                ).fetchall()
                
                # Get hourly activity for today
                hourly_data = conn.execute(
                    """SELECT strftime('%H', timestamp) as hour, COUNT(*) as count 
                       FROM events 
                       WHERE event_type = 'button_press' AND date(timestamp) = date('now')
                       GROUP BY hour ORDER BY hour"""
                ).fetchall()
                
                # Find peak hour
                peak_hour = "N/A"
                if hourly_data:
                    peak_hour = max(hourly_data, key=lambda x: x[1])[0] + ":00"
                
                # Calculate daily average (simple estimation)
                daily_average = 0
                if total_button_presses > 0:
                    # Get days since first event
                    first_event = conn.execute(
                        "SELECT date(timestamp) FROM events ORDER BY timestamp ASC LIMIT 1"
                    ).fetchone()
                    if first_event:
                        from datetime import date
                        first_date = datetime.strptime(first_event[0], '%Y-%m-%d').date()
                        days_active = (date.today() - first_date).days + 1
                        daily_average = total_button_presses / max(1, days_active)
                
                return {
                    "total_button_presses": total_button_presses,
                    "today_button_presses": today_button_presses,
                    "daily_average": daily_average,
                    "peak_hour": peak_hour,
                    "total_viewing_minutes": total_viewing_minutes,
                    "yesterday_viewing_minutes": yesterday_viewing_minutes,
                    "recent_activity": [
                        {
                            "action": f"{event[0]} - {event[1]}" + (f" ({event[2]})" if event[2] else ""),
                            "timestamp": event[3]
                        }
                        for event in recent_events
                    ]
                }
                
        except sqlite3.Error as e:
            self.logger.error("Error getting statistics summary: %s", e)
            return {}
    
    def get_hourly_data(self, date_str: str = None) -> Dict:
        """Get hourly button press data for a specific date (YYYY-MM-DD format)."""
        if not self.enabled:
            return {}
        
        try:
            if date_str is None:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_file) as conn:
                # Get hourly activity for the specified date
                hourly_data = conn.execute(
                    """SELECT strftime('%H', timestamp) as hour, COUNT(*) as count 
                       FROM events 
                       WHERE event_type = 'button_press' AND date(timestamp) = ?
                       GROUP BY hour ORDER BY hour""",
                    (date_str,)
                ).fetchall()
                
                # Convert to dictionary with all 24 hours
                hourly_dict = {}
                for i in range(24):
                    hour_str = f"{i:02d}"
                    hourly_dict[hour_str] = {"button_presses": 0, "interruptions": 0}
                
                # Fill in actual data
                for hour, count in hourly_data:
                    hourly_dict[hour]["button_presses"] = count
                
                return hourly_dict
                
        except sqlite3.Error as e:
            self.logger.error("Error getting hourly data: %s", e)
            return {}
            # Fallback to aggregated stats
            with self.stats_lock:
                return {
                    "total_button_presses": self._stats.get("button_presses", {}).get("total", 0),
                    "today_button_presses": 0,
                    "daily_average": 0,
                    "peak_hour": "N/A",
                    "recent_activity": []
                }
    
    def get_detailed_events(self, limit: int = 100, event_type: str = None) -> list:
        """Get detailed event history from SQLite."""
        if not self.enabled:
            return []
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                query = "SELECT * FROM events"
                params = []
                
                if event_type:
                    query += " WHERE event_type = ?"
                    params.append(event_type)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                events = conn.execute(query, params).fetchall()
                
                # Convert to list of dictionaries
                columns = ['id', 'timestamp', 'event_type', 'action', 'details', 
                          'video_file', 'duration', 'source', 'created_at']
                return [dict(zip(columns, event)) for event in events]
                
        except sqlite3.Error as e:
            self.logger.error("Error getting detailed events: %s", e)
            return []
    
    def get_cooldown_status(self) -> Dict:
        """Get current cooldown status for button presses."""
        if not self.last_button_press:
            return {
                "cooldown_active": False,
                "cooldown_period": self.cooldown_seconds,
                "time_remaining": 0,
                "last_press": None
            }
        
        now = datetime.now()
        time_since_last = (now - self.last_button_press).total_seconds()
        time_remaining = max(0, self.cooldown_seconds - time_since_last)
        
        return {
            "cooldown_active": time_remaining > 0,
            "cooldown_period": self.cooldown_seconds,
            "time_remaining": int(time_remaining),
            "last_press": self.last_button_press.isoformat()
        }
    
    def reset_stats(self):
        """Reset all statistics (both SQLite and JSON)."""
        if not self.enabled:
            return
        
        try:
            # Clear SQLite database
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("DELETE FROM events")
                conn.commit()
            
            # Reset aggregated stats
            with self.stats_lock:
                self._stats = self._load_stats()
            
            self._save_stats_to_file()
            self.logger.info("Statistics reset successfully")
            
        except sqlite3.Error as e:
            self.logger.error("Error resetting statistics: %s", e)
