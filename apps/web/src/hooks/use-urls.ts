/**
 * Custom hook for URL API operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { AxiosError } from 'axios';
import { toast } from 'sonner';
import api from '@/lib/api';
import type { CreateUrlRequest, Url, UrlWithLogs, PaginatedUrlResponse } from '@/types/url.types';

/**
 * Fetch all URLs with pagination
 */
export const useUrls = (page: number = 1, pageSize: number = 10, accountId?: string) => {
  return useQuery<PaginatedUrlResponse, Error>({
    queryKey: ['urls', page, pageSize, accountId],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (accountId) {
        params.account_id = accountId;
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
 *
 * Uses wrapped mutateAsync to avoid deprecated onSuccess/onError options.
 */
export const useCreateUrl = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    Url,
    AxiosError<{ detail?: string; error?: string }>,
    CreateUrlRequest
  >({
    mutationFn: async (data: CreateUrlRequest) => {
      const response = await api.post('/api/urls', data);
      return response.data;
    },
  });

  const wrappedMutateAsync: typeof mutation.mutateAsync = async (variables, options) => {
    try {
      const data = await mutation.mutateAsync(variables, options);

      // Invalidate URLs query to refetch the list
      await queryClient.invalidateQueries({ queryKey: ['urls'] });

      toast('URL Created Successfully! 🎉', {
        description: `URL endpoint created at ${data.path}`,
      });

      return data;
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
      const status = axiosError.response?.status;
      const backendMessage = axiosError.response?.data?.detail || axiosError.response?.data?.error;

      if (status === 400) {
        toast.error('Invalid URL Request', {
          description: backendMessage || 'Please check the URL details and try again.',
        });
      } else if (status && status >= 500) {
        toast.error('Server Error', {
          description: backendMessage || 'Something went wrong on our side while creating the URL.',
        });
      } else {
        toast.error('Failed to Create URL', {
          description: backendMessage || axiosError.message || 'Failed to create URL.',
        });
      }

      throw error;
    }
  };

  return {
    ...mutation,
    mutateAsync: wrappedMutateAsync,
  };
};

/**
 * Update a URL
 *
 * Uses wrapped mutateAsync to avoid deprecated onSuccess/onError options.
 */
export const useUpdateUrl = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    Url,
    AxiosError<{ detail?: string; error?: string }>,
    { id: string; data: CreateUrlRequest }
  >({
    mutationFn: async ({ id, data }) => {
      const response = await api.put(`/api/urls/${id}`, data);
      return response.data;
    },
  });

  const wrappedMutateAsync: typeof mutation.mutateAsync = async (variables, options) => {
    try {
      const data = await mutation.mutateAsync(variables, options);

      // Invalidate queries
      await queryClient.invalidateQueries({ queryKey: ['urls'] });
      await queryClient.invalidateQueries({ queryKey: ['url', data.id] });

      toast('URL Updated', {
        description: 'Your URL has been updated successfully.',
      });

      return data;
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
      const status = axiosError.response?.status;
      const backendMessage = axiosError.response?.data?.detail || axiosError.response?.data?.error;

      if (status === 400) {
        toast.error('Invalid URL Request', {
          description: backendMessage || 'Please check the URL details and try again.',
        });
      } else if (status && status >= 500) {
        toast.error('Server Error', {
          description: backendMessage || 'Something went wrong on our side while updating the URL.',
        });
      } else {
        toast.error('Update Failed', {
          description: backendMessage || axiosError.message || 'Failed to update URL.',
        });
      }

      throw error;
    }
  };

  return {
    ...mutation,
    mutateAsync: wrappedMutateAsync,
  };
};

/**
 * Delete a URL
 *
 * Uses wrapped mutateAsync to avoid deprecated onSuccess/onError options.
 */
export const useDeleteUrl = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, AxiosError<{ detail?: string; error?: string }>, string>({
    mutationFn: async (urlId: string) => {
      await api.delete(`/api/urls/${urlId}`);
    },
  });

  const wrappedMutateAsync: typeof mutation.mutateAsync = async (variables, options) => {
    try {
      const result = await mutation.mutateAsync(variables, options);

      // Invalidate URLs query to refetch the list
      await queryClient.invalidateQueries({ queryKey: ['urls'] });

      toast('URL Deleted', {
        description: 'The URL has been removed successfully.',
      });

      return result;
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
      const status = axiosError.response?.status;
      const backendMessage = axiosError.response?.data?.detail || axiosError.response?.data?.error;

      if (status === 400) {
        toast.error('Cannot Delete URL', {
          description: backendMessage || 'Please check the URL and try again.',
        });
      } else if (status && status >= 500) {
        toast.error('Server Error', {
          description: backendMessage || 'Something went wrong on our side while deleting the URL.',
        });
      } else {
        toast.error('Delete Failed', {
          description: backendMessage || axiosError.message || 'Failed to delete URL.',
        });
      }

      throw error;
    }
  };

  return {
    ...mutation,
    mutateAsync: wrappedMutateAsync,
  };
};
