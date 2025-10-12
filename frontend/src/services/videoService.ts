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
    const response = await api.get<PlaybackStatus>('/video/status');
    return response.data || { is_playing: false };
  },

  // Play a video
  async play(videoId: number): Promise<ApiResponse> {
    return api.post('/video/play', { video_id: videoId });
  },

  // Stop playback
  async stop(): Promise<ApiResponse> {
    return api.post('/video/stop');
  },

  // Pause playback
  async pause(): Promise<ApiResponse> {
    return api.post('/video/pause');
  },

  // Resume playback
  async resume(): Promise<ApiResponse> {
    return api.post('/video/resume');
  },

  // Set volume
  async setVolume(volume: number): Promise<ApiResponse> {
    return api.post('/video/volume', { volume });
  },

  // Upload video
  async upload(file: File, onProgress?: (progress: number) => void): Promise<ApiResponse> {
    return api.uploadFile('/video/upload', file, onProgress);
  },

  // Delete video
  async delete(videoId: number): Promise<ApiResponse> {
    return api.delete(`/video/${videoId}`);
  },

  // Update video info
  async update(videoId: number, data: Partial<Video>): Promise<ApiResponse> {
    return api.put(`/video/${videoId}`, data);
  },
};
