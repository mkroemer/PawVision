// Custom hook for fetching videos

import { useState, useEffect, useCallback } from 'react';
import { videoService } from '@/services/videoService';
import type { Video } from '@/types';

const PAGE_SIZE = 20;

export const useVideos = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  const fetchVideos = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await videoService.getVideos(1, PAGE_SIZE);
      setVideos(result.videos);
      setPage(1);
      setHasMore(result.pagination.has_more);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch videos');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore) return;
    try {
      setLoadingMore(true);
      const nextPage = page + 1;
      const result = await videoService.getVideos(nextPage, PAGE_SIZE);
      setVideos((prev) => [...prev, ...result.videos]);
      setPage(nextPage);
      setHasMore(result.pagination.has_more);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch videos');
    } finally {
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, page]);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  // Refetch when page becomes visible again (tab switching)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchVideos();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchVideos]);

  return { videos, loading, loadingMore, hasMore, error, refetch: fetchVideos, loadMore };
};
