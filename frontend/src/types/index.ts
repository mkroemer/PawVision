// Type definitions for PawVision

export interface Video {
  id: number;
  title: string;
  filename: string;
  path: string;
  duration: number;
  source: 'local' | 'youtube';
  youtube_url?: string;
  thumbnail?: string;
  added_date: string;
  custom_start_time?: number;
  custom_end_time?: number | null;
}

export interface PlaybackStatus {
  is_playing: boolean;
  current_video?: Video;
  position?: number;
  volume?: number;
  next_scheduled_play?: string | null;
}

export interface Statistics {
  total_plays: number;
  total_duration: number;
  favorite_video?: Video;
  plays_by_day: Array<{ date: string; count: number }>;
  plays_by_video: Array<{ video: Video; count: number }>;
}

export interface Config {
  gpio_enabled: boolean;
  auto_play: boolean;
  volume: number;
  playback_duration_minutes: number;
  youtube_quality: string;
  play_schedule: string[];
  night_mode_start: string;
  night_mode_end: string;
  night_mode_disable_playback: boolean;
  night_mode_volume: number;
  motion_sensor_enabled: boolean;
  motion_stop_enabled: boolean;
  motion_stop_timeout_seconds: number;
  [key: string]: any;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
}

export interface UploadProgress {
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  message?: string;
}
