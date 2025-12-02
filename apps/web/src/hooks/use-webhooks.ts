/**
 * Custom hook for webhook API operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { AxiosError } from 'axios';
import { toast } from 'sonner';
import api from '@/lib/api';
import type { CreateCronWebhookRequest, CronWebhookResponse, Webhook } from '@/types/webhook.types';

/**
 * Fetch all webhooks with pagination
 */
export const useWebhooks = (limit: number = 100, offset: number = 0) => {
  return useQuery<Webhook[], Error>({
    queryKey: ['webhooks', limit, offset],
    queryFn: async () => {
      const response = await api.get('/api/schedules', {
        params: { limit, offset },
      });
      return response.data;
    },
  });
};

/**
 * Fetch a single webhook by ID
 */
export const useWebhook = (webhookId: string) => {
  return useQuery<Webhook, Error>({
    queryKey: ['webhook', webhookId],
    queryFn: async () => {
      const response = await api.get(`/api/schedules/${webhookId}`);
      return response.data;
    },
    enabled: !!webhookId,
  });
};

/**
 * Create a new webhook with job
 *
 * Note: React Query v5 discourages using onSuccess/onError in the hook options.
 * We wrap mutateAsync to keep side effects (toasts, cache invalidation) here.
 */
export const useCreateWebhook = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    CronWebhookResponse,
    AxiosError<{ detail?: string; error?: string }>,
    CreateCronWebhookRequest
  >({
    mutationFn: async (data: CreateCronWebhookRequest) => {
      const response = await api.post('/api/schedules', data);
      return response.data;
    },
  });

  const wrappedMutateAsync: typeof mutation.mutateAsync = async (variables, options) => {
    try {
      const data = await mutation.mutateAsync(variables, options);

      // Invalidate webhooks query to refetch the list
      await queryClient.invalidateQueries({ queryKey: ['webhooks'] });

      toast('Webhook Created Successfully! 🎉', {
        description: `Job "${data.job.name}" and webhook have been created and scheduled.`,
      });

      return data;
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
      const status = axiosError.response?.status;
      const backendMessage = axiosError.response?.data?.detail || axiosError.response?.data?.error;

      if (status === 400) {
        toast.error('Invalid Request', {
          description: backendMessage || 'Please check the form fields and try again.',
        });
      } else if (status && status >= 500) {
        toast.error('Server Error', {
          description:
            backendMessage || 'Something went wrong on our side while creating the webhook.',
        });
      } else {
        toast.error('Failed to Create Webhook', {
          description: backendMessage || axiosError.message || 'Failed to create webhook.',
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
 * Update a webhook
 *
 * See note in useCreateWebhook about wrapped mutateAsync.
 */
export const useUpdateWebhook = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    Webhook,
    AxiosError<{ detail?: string; error?: string }>,
    {
      id: string;
      data: Partial<Webhook> & {
        job?: {
          name?: string;
          schedule?: string;
          timezone?: string;
          enabled?: boolean;
        };
      };
    }
  >({
    mutationFn: async ({ id, data }) => {
      const response = await api.put(`/api/schedules/${id}`, data);
      return response.data;
    },
  });

  const wrappedMutateAsync: typeof mutation.mutateAsync = async (variables, options) => {
    try {
      const data = await mutation.mutateAsync(variables, options);

      // Invalidate queries
      await queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      await queryClient.invalidateQueries({ queryKey: ['webhook', data.id] });

      toast('Webhook Updated', {
        description: 'Your webhook has been updated successfully.',
      });

      return data;
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
      const status = axiosError.response?.status;
      const backendMessage = axiosError.response?.data?.detail || axiosError.response?.data?.error;

      if (status === 400) {
        toast.error('Invalid Request', {
          description: backendMessage || 'Please check the form fields and try again.',
        });
      } else if (status && status >= 500) {
        toast.error('Server Error', {
          description:
            backendMessage || 'Something went wrong on our side while updating the webhook.',
        });
      } else {
        toast.error('Update Failed', {
          description: backendMessage || axiosError.message || 'Failed to update webhook.',
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
 * Delete a webhook
 *
 * Wrapped mutateAsync to centralize side effects.
 */
export const useDeleteWebhook = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation<void, AxiosError<{ detail?: string }>, string>({
    mutationFn: async (webhookId: string) => {
      await api.delete(`/api/schedules/${webhookId}`);
    },
  });

  const wrappedMutateAsync: typeof mutation.mutateAsync = async (variables, options) => {
    try {
      const result = await mutation.mutateAsync(variables, options);

      // Invalidate webhooks query to refetch the list
      await queryClient.invalidateQueries({ queryKey: ['webhooks'] });

      toast('Webhook Deleted', {
        description: 'The webhook has been removed successfully.',
      });

      return result;
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail || axiosError.message || 'Failed to delete webhook';

      toast.error('Delete Failed', {
        description: message,
      });

      throw error;
    }
  };

  return {
    ...mutation,
    mutateAsync: wrappedMutateAsync,
  };
};
