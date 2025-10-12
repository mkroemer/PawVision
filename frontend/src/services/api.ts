// API service for making HTTP requests

import type { ApiResponse } from '@/types';

class ApiService {
  private baseUrl = '/api';

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        // Return error data in the expected format
        return {
          success: false,
          message: data.error || data.message || `Request failed with status ${response.status}`,
          data: data
        };
      }

      // Backend might return { status: 'success' } instead of { success: true }
      // Normalize the response
      if ('status' in data && !('success' in data)) {
        return {
          success: data.status === 'success',
          message: data.message,
          data: data
        };
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      // Return error in expected format instead of throwing
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async put<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async uploadFile<T>(
    endpoint: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append('file', file);

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        try {
          const responseData = JSON.parse(xhr.responseText);
          
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve({
              success: true,
              message: responseData.success || responseData.message,
              data: responseData
            });
          } else {
            // Parse error message from response
            const errorMessage = responseData.error || responseData.message || `Upload failed with status ${xhr.status}`;
            reject(new Error(errorMessage));
          }
        } catch (e) {
          // If response isn't JSON, use generic message
          reject(new Error(xhr.status >= 200 && xhr.status < 300 ? 'Upload completed' : 'Upload failed'));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Network error during upload')));
      xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')));

      xhr.open('POST', `${this.baseUrl}${endpoint}`);
      xhr.send(formData);
    });
  }
}

export const api = new ApiService();
