/**
 * Custom hook for URL API operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { CreateUrlRequest, Url, UrlWithLogs, PaginatedUrlResponse } from '@/types/url.types';

/**
 * Fetch all URLs with pagination
 */
export const useUrls = (page: number = 1, pageSize: number = 10, projectId?: string) => {
  return useQuery<PaginatedUrlResponse, Error>({
    queryKey: ['urls', page, pageSize, projectId],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (projectId) {
        params.project_id = projectId;
      }
      const response = await api.get('/api/urls', { params });
      return response.data;
    },
  });
};

/**
 * Fetch a single URL by ID
 */
export const useUrl = (urlId: string) => {
  return useQuery<Url, Error>({
    queryKey: ['url', urlId],
    queryFn: async () => {
      const response = await api.get(`/api/urls/${urlId}`);
      return response.data;
    },
    enabled: !!urlId,
  });
};

/**
 * Fetch URL logs with pagination
 */
export const useUrlLogs = (urlId: string, page: number = 1, pageSize: number = 50) => {
  return useQuery<UrlWithLogs, Error>({
    queryKey: ['url-logs', urlId, page, pageSize],
    queryFn: async () => {
      const response = await api.get(`/api/urls/${urlId}/logs`, {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
    enabled: !!urlId,
  });
};

/**
 * Create a new URL
 */
export const useCreateUrl = () => {
  const queryClient = useQueryClient();

  return useMutation<Url, Error, CreateUrlRequest>({
    mutationFn: async (data: CreateUrlRequest) => {
      const response = await api.post('/api/urls', data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate URLs query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['urls'] });

      toast({
        title: 'URL Created Successfully! 🎉',
        description: `URL endpoint created at ${data.path}`,
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to create URL';
      toast({
        title: 'Failed to Create URL',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Update a URL
 */
export const useUpdateUrl = () => {
  const queryClient = useQueryClient();

  return useMutation<Url, Error, { id: string; data: CreateUrlRequest }>({
    mutationFn: async ({ id, data }) => {
      const response = await api.put(`/api/urls/${id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['urls'] });
      queryClient.invalidateQueries({ queryKey: ['url', data.id] });

      toast({
        title: 'URL Updated',
        description: 'Your URL has been updated successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to update URL';
      toast({
        title: 'Update Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Delete a URL
 */
export const useDeleteUrl = () => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (urlId: string) => {
      await api.delete(`/api/urls/${urlId}`);
    },
    onSuccess: () => {
      // Invalidate URLs query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['urls'] });

      toast({
        title: 'URL Deleted',
        description: 'The URL has been removed successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to delete URL';
      toast({
        title: 'Delete Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};
