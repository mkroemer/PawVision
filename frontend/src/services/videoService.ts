// Video API service

import { api } from './api';
import type { Video, PlaybackStatus, ApiResponse, VideoPagination } from '@/types';

interface VideoListResponse {
  videos: Video[];
  pagination: VideoPagination;
}

export const videoService = {
  // Get videos with optional pagination
  async getVideos(page: number = 1, perPage: number = 20): Promise<VideoListResponse> {
    const response = await api.get<any>(`/video/list?paginated=1&page=${page}&per_page=${perPage}`);
    const data = response.data || response;

    if (!data.success) {
      throw new Error(data.error || data.message || 'Failed to fetch videos');
    }

    return {
      videos: data.videos || [],
      pagination: data.pagination || {
        page,
        per_page: perPage,
        total: 0,
        has_more: false,
      },
    };
  },

  // Get playback status
  async getStatus(): Promise<PlaybackStatus> {
    const response = await api.get<any>('/status');
    // Backend returns 'playing', but frontend expects 'is_playing'
    const data = response.data || response;
    return {
      is_playing: data.playing !== undefined ? data.playing : (data.is_playing || false),
      paused: data.paused || false,
      current_video: data.current_video
    };
  },

  // Play a video by path
  async play(videoPath: string): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('path', videoPath);
    
    const response = await fetch('/api/play', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to play video');
    }

    return {
      success: true,
      message: 'Playing video',
      data: data,
    };
  },

  // Stop playback
  async stop(): Promise<ApiResponse> {
    return api.post('/stop');
  },

  // Next video (random)
  async next(): Promise<ApiResponse> {
    return api.post('/next');
  },

  // Pause playback
  async pause(): Promise<ApiResponse> {
    return api.post('/pause');
  },

  // Resume playback
  async resume(): Promise<ApiResponse> {
    return api.post('/resume');
  },

  // Set volume
  async setVolume(volume: number): Promise<ApiResponse> {
    return api.post('/volume', { volume });
  },

  // Upload video
  async upload(file: File, onProgress?: (progress: number) => void): Promise<ApiResponse> {
    return api.uploadFile('/video/upload', file, onProgress);
  },

  // Delete video
  async delete(videoPath: string): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('path', videoPath);
    
    const response = await fetch('/api/video/delete', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to delete video');
    }

    return {
      success: true,
      message: data.success || 'Video deleted successfully',
      data: data,
    };
  },

  // Update video info
  async update(videoPath: string, data: { title?: string; startTime?: number; endOffsetSeconds?: number }): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('path', videoPath);
    if (data.title !== undefined) formData.append('title', data.title);
    if (data.startTime !== undefined) formData.append('custom_start_time', String(data.startTime));
    if (data.endOffsetSeconds !== undefined) formData.append('custom_end_offset', String(data.endOffsetSeconds));

    const response = await fetch('/api/video/update', { method: 'POST', body: formData });
    const responseData = await response.json();
    if (!response.ok) throw new Error(responseData.error || 'Failed to update video');
    return { success: true, message: responseData.message, data: responseData };
  },
};
