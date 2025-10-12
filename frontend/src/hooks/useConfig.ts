// Custom hook for configuration

import { useState, useEffect, useCallback } from 'react';
import { configService } from '@/services/configService';
import type { Config } from '@/types';

export const useConfig = () => {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await configService.get();
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch config');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = useCallback(async (updates: Partial<Config>) => {
    try {
      setError(null);
      const response = await configService.update(updates);
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to update config');
      }
      
      await fetchConfig();
      return response;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update config';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchConfig]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return { config, loading, error, refetch: fetchConfig, updateConfig };
};
