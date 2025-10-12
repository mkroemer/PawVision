// YouTube API service

import { api } from './api';
import type { ApiResponse } from '@/types';

export const youtubeService = {
  // Download YouTube video (actually adds and downloads it)
  async download(
    url: string, 
    startTime?: number, 
    endTime?: number,
    quality: string = '720p'
  ): Promise<ApiResponse> {
    return api.post('/youtube/add', { 
      url,
      quality,
      download: true, // This tells the backend to download the video
      start_time: startTime || 0,
      end_time: endTime
    });
  },

  // Add YouTube video without downloading (streaming only)
  async add(
    url: string, 
    startTime?: number,
    endTime?: number,
    quality: string = '720p', 
    download: boolean = false
  ): Promise<ApiResponse> {
    return api.post('/youtube/add', { 
      url,
      quality,
      download,
      start_time: startTime || 0,
      end_time: endTime
    });
  },

  // Get download progress
  async getProgress(taskId: string): Promise<ApiResponse> {
    return api.get(`/youtube/progress/${taskId}`);
  },

  // Cancel download
  async cancel(taskId: string): Promise<ApiResponse> {
    return api.post(`/youtube/cancel/${taskId}`);
  },

  // Validate YouTube URL
  async validate(url: string): Promise<ApiResponse> {
    return api.post('/youtube/validate', { url });
  },
};
