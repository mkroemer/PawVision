// Configuration API service

import { api } from './api';
import type { Config, ApiResponse } from '@/types';

export const configService = {
  // Get configuration
  async get(): Promise<Config> {
    const response = await api.get<Config>('/config');
    return response.data || {} as Config;
  },

  // Update configuration
  async update(config: Partial<Config>): Promise<ApiResponse> {
    return api.post('/config/update', config);
  },

  // Reset configuration to defaults
  async reset(): Promise<ApiResponse> {
    return api.post('/config/reset');
  },

  // Test GPIO
  async testGpio(): Promise<ApiResponse> {
    return api.post('/config/test-gpio');
  },
};
