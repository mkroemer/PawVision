// Statistics API service

import { api } from './api';
import type { ApiResponse } from '@/types';

export interface StatisticsSummary {
  total_plays: number;
  total_duration: number;
  total_videos: number;
  favorite_video?: {
    title: string;
    play_count: number;
  };
  recent_plays: Array<{
    video_title: string;
    timestamp: string;
    duration: number;
  }>;
}

export interface PlaysByDay {
  date: string;
  plays: number;
}

export interface PlaysByVideo {
  video_title: string;
  play_count: number;
  total_duration: number;
}

export const statisticsService = {
  // Get statistics summary
  async getSummary(): Promise<StatisticsSummary> {
    const response = await api.get<StatisticsSummary>('/statistics/summary');
    return response.data || {
      total_plays: 0,
      total_duration: 0,
      total_videos: 0,
      recent_plays: [],
    };
  },

  // Get plays by day for chart
  async getPlaysByDay(days: number = 30): Promise<PlaysByDay[]> {
    const response = await api.get<PlaysByDay[]>(`/statistics/plays-by-day?days=${days}`);
    return response.data || [];
  },

  // Get plays by video for chart
  async getPlaysByVideo(limit: number = 10): Promise<PlaysByVideo[]> {
    const response = await api.get<PlaysByVideo[]>(`/statistics/plays-by-video?limit=${limit}`);
    return response.data || [];
  },

  // Get detailed statistics
  async getDetailed(startDate?: string, endDate?: string): Promise<ApiResponse> {
    const params = new URLSearchParams();
    if (startDate) params.append('start', startDate);
    if (endDate) params.append('end', endDate);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/statistics/detailed${query}`);
  },

  // Reset statistics
  async reset(): Promise<ApiResponse> {
    return api.post('/statistics/reset');
  },
};
