// Video API service

import { api } from './api';
import type { Video, PlaybackStatus, ApiResponse } from '@/types';

export const videoService = {
  // Get all videos
  async getVideos(): Promise<Video[]> {
    const response = await api.get<Video[]>('/video/list');
    // The /video/list endpoint returns an array directly, not wrapped in { data: [...] }
    // So if response is an array, use it directly; otherwise check response.data
    if (Array.isArray(response)) {
      return response;
    }
    return response.data || [];
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
  async update(videoId: number, data: Partial<Video>): Promise<ApiResponse> {
    return api.put(`/video/${videoId}`, data);
  },
};
