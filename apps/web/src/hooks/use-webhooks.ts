/**
 * Custom hook for webhook API operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { CreateCronWebhookRequest, CronWebhookResponse, Webhook } from '@/types/webhook.types';

/**
 * Fetch all webhooks with pagination
 */
export const useWebhooks = (limit: number = 100, offset: number = 0) => {
  return useQuery<Webhook[], Error>({
    queryKey: ['webhooks', limit, offset],
    queryFn: async () => {
      const response = await api.get('/api/webhooks', {
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
      const response = await api.get(`/api/webhooks/${webhookId}`);
      return response.data;
    },
    enabled: !!webhookId,
  });
};

/**
 * Create a new webhook with job
 */
export const useCreateWebhook = () => {
  const queryClient = useQueryClient();

  return useMutation<CronWebhookResponse, Error, CreateCronWebhookRequest>({
    mutationFn: async (data: CreateCronWebhookRequest) => {
      const response = await api.post('/api/webhooks', data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate webhooks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });

      toast({
        title: 'Webhook Created Successfully! 🎉',
        description: `Job "${data.job.name}" and webhook have been created and scheduled.`,
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to create webhook';
      toast({
        title: 'Failed to Create Webhook',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Update a webhook
 */
export const useUpdateWebhook = () => {
  const queryClient = useQueryClient();

  return useMutation<
    Webhook,
    Error,
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
      const response = await api.put(`/api/webhooks/${id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      queryClient.invalidateQueries({ queryKey: ['webhook', data.id] });

      toast({
        title: 'Webhook Updated',
        description: 'Your webhook has been updated successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to update webhook';
      toast({
        title: 'Update Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Delete a webhook
 */
export const useDeleteWebhook = () => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (webhookId: string) => {
      await api.delete(`/api/webhooks/${webhookId}`);
    },
    onSuccess: () => {
      // Invalidate webhooks query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });

      toast({
        title: 'Webhook Deleted',
        description: 'The webhook has been removed successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to delete webhook';
      toast({
        title: 'Delete Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};
