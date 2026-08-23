// YouTube API service

import { api } from './api';
import type { ApiResponse } from '@/types';

export const youtubeService = {
  // Download YouTube video (actually adds and downloads it)
  async download(
    url: string, 
    startTime?: number, 
    endOffsetSeconds?: number,
    quality: string = '720p'
  ): Promise<ApiResponse> {
    return api.post('/youtube/add', { 
      url,
      quality,
      download: true, // This tells the backend to download the video
      start_time: startTime || 0,
      end_offset_seconds: endOffsetSeconds
    });
  },

  // Add YouTube video without downloading (streaming only)
  async add(
    url: string, 
    startTime?: number,
    endOffsetSeconds?: number,
    quality: string = '720p', 
    download: boolean = false
  ): Promise<ApiResponse> {
    return api.post('/youtube/add', { 
      url,
      quality,
      download,
      start_time: startTime || 0,
      end_offset_seconds: endOffsetSeconds
    });
  },

  // Get download progress
  async getProgress(taskId: string): Promise<ApiResponse> {
    return api.get(`/youtube/download/progress/${taskId}`);
  },

  // Validate YouTube URL
  async validate(url: string): Promise<ApiResponse> {
    return api.post('/youtube/validate', { url });
  },
};
