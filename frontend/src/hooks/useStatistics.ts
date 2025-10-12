// Custom hook for statistics data

import { useState, useEffect, useCallback } from 'react';
import { statisticsService, StatisticsSummary, PlaysByDay, PlaysByVideo } from '@/services/statisticsService';

export const useStatistics = () => {
  const [summary, setSummary] = useState<StatisticsSummary | null>(null);
  const [playsByDay, setPlaysByDay] = useState<PlaysByDay[]>([]);
  const [playsByVideo, setPlaysByVideo] = useState<PlaysByVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [summaryData, dayData, videoData] = await Promise.all([
        statisticsService.getSummary(),
        statisticsService.getPlaysByDay(30),
        statisticsService.getPlaysByVideo(10),
      ]);

      setSummary(summaryData);
      setPlaysByDay(dayData);
      setPlaysByVideo(videoData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return { summary, playsByDay, playsByVideo, loading, error, refetch: fetchStatistics };
};
