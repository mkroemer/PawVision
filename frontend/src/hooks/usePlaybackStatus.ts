// Custom hook for video playback status

import { useState, useEffect, useCallback } from 'react';
import { videoService } from '@/services/videoService';
import type { PlaybackStatus } from '@/types';

export const usePlaybackStatus = (autoRefresh = true, interval = 5000) => {
  const [status, setStatus] = useState<PlaybackStatus>({ is_playing: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setError(null);
      const data = await videoService.getStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();

    if (autoRefresh) {
      const intervalId = setInterval(fetchStatus, interval);
      return () => clearInterval(intervalId);
    }
  }, [fetchStatus, autoRefresh, interval]);

  // Refetch when page becomes visible again (tab switching)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchStatus();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchStatus]);

  return { status, loading, error, refetch: fetchStatus };
};
