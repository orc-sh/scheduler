/**
 * Custom hook for Collection API operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';
import type {
  CreateCollectionRequest,
  CreateCollectionRunRequest,
  CreateWebhookRequest,
  Collection,
  CollectionWithRuns,
  CollectionReport,
  CollectionReportWithResults,
  CollectionRun,
  CollectionRunWithReports,
  PaginatedCollectionResponse,
  UpdateCollectionRequest,
  UpdateWebhookRequest,
  Webhook,
} from '@/types/collection.types';

/**
 * Fetch all collections with pagination
 */
export const useCollections = (page: number = 1, pageSize: number = 10, projectId?: string) => {
  return useQuery<PaginatedCollectionResponse, Error>({
    queryKey: ['collections', page, pageSize, projectId],
    queryFn: async () => {
      const params: any = { page, page_size: pageSize };
      if (projectId) params.project_id = projectId;
      const response = await api.get('/api/collections', { params });
      return response.data;
    },
  });
};

/**
 * Fetch a single collection configuration by ID
 */
export const useCollection = (collectionId: string) => {
  return useQuery<CollectionWithRuns, Error>({
    queryKey: ['collection', collectionId],
    queryFn: async () => {
      const response = await api.get(`/api/collections/${collectionId}`);
      return response.data;
    },
    enabled: !!collectionId,
  });
};

/**
 * Fetch all runs for a configuration
 */
export const useCollectionRunsByCollection = (collectionId: string) => {
  return useQuery<CollectionRun[], Error>({
    queryKey: ['collection-runs', collectionId],
    queryFn: async () => {
      const response = await api.get(`/api/collections/${collectionId}/runs`);
      return response.data;
    },
    enabled: !!collectionId,
  });
};

/**
 * Fetch a single collection run by ID
 */
export const useCollectionRun = (runId: string, includeResults: boolean = false) => {
  return useQuery<CollectionRunWithReports, Error>({
    queryKey: ['collection-run', runId, includeResults],
    queryFn: async () => {
      const params: any = {};
      if (includeResults) {
        params.include_results = true;
      }
      const response = await api.get(`/api/collections/runs/${runId}`, { params });
      return response.data;
    },
    enabled: !!runId,
  });
};

/**
 * Fetch all reports for a run
 */
export const useCollectionReports = (runId: string) => {
  return useQuery<CollectionReport[], Error>({
    queryKey: ['collection-reports', runId],
    queryFn: async () => {
      const response = await api.get(`/api/collections/runs/${runId}/reports`);
      return response.data;
    },
    enabled: !!runId,
  });
};

/**
 * Fetch a single report with results
 */
export const useCollectionReport = (reportId: string, page: number = 1, pageSize: number = 50) => {
  return useQuery<CollectionReportWithResults, Error>({
    queryKey: ['collection-report', reportId, page, pageSize],
    queryFn: async () => {
      const response = await api.get(`/api/collections/reports/${reportId}`, {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
    enabled: !!reportId,
  });
};

/**
 * Create a new collection configuration
 */
export const useCreateCollection = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<Collection, Error, CreateCollectionRequest>({
    mutationFn: async (data: CreateCollectionRequest) => {
      const response = await api.post('/api/collections', data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate collections query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['collections'] });

      toast({
        title: 'Collection Created! 🚀',
        description: 'Your webhook collection has been created successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to create benchmark configuration';
      toast({
        title: 'Failed to Create Collection',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Update a collection configuration
 */
export const useUpdateCollection = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<Collection, Error, { id: string; data: UpdateCollectionRequest }>({
    mutationFn: async ({ id, data }) => {
      const response = await api.put(`/api/collections/${id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['collection', data.id] });

      toast({
        title: 'Collection Updated',
        description: 'Your webhook collection has been updated successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to update benchmark configuration';
      toast({
        title: 'Update Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Delete a collection configuration
 */
export const useDeleteCollection = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<void, Error, string>({
    mutationFn: async (collectionId: string) => {
      await api.delete(`/api/collections/${collectionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });

      toast({
        title: 'Collection Deleted',
        description: 'The webhook collection has been removed successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to delete benchmark configuration';
      toast({
        title: 'Delete Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Create a new collection run from a collection
 */
export const useCreateCollectionRun = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<
    CollectionRun,
    Error,
    { collectionId: string; data: CreateCollectionRunRequest }
  >({
    mutationFn: async ({ collectionId, data }) => {
      const response = await api.post(`/api/collections/${collectionId}/runs`, data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['collection', variables.collectionId] });
      queryClient.invalidateQueries({ queryKey: ['collection-runs', variables.collectionId] });
      queryClient.invalidateQueries({ queryKey: ['collection-run', data.id] });

      toast({
        title: 'Test Started! 🚀',
        description: 'Your collection run has been created and started.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to start test';
      toast({
        title: 'Failed to Start Test',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Manually trigger a collection run
 */
export const useRunCollection = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<CollectionRun, Error, string>({
    mutationFn: async (runId: string) => {
      const response = await api.post(`/api/collections/runs/${runId}/run`);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['collection-runs'] });
      queryClient.invalidateQueries({ queryKey: ['collection-run', data.id] });
      queryClient.invalidateQueries({ queryKey: ['collection-reports', data.id] });

      toast({
        title: 'Test Started',
        description: `Load test run is now running.`,
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Failed to start benchmark';
      toast({
        title: 'Failed to Start Benchmark',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Delete a collection run
 */
export const useDeleteCollectionRun = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<void, Error, string>({
    mutationFn: async (runId: string) => {
      await api.delete(`/api/collections/runs/${runId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-runs'] });
      queryClient.invalidateQueries({ queryKey: ['collections'] });

      toast({
        title: 'Test Run Deleted',
        description: 'The test run has been removed successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to delete benchmark run';
      toast({
        title: 'Delete Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Create a new webhook for a collection
 */
export const useCreateWebhook = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<Webhook, Error, { collectionId: string; data: CreateWebhookRequest }>({
    mutationFn: async ({ collectionId, data }) => {
      const response = await api.post(`/api/collections/${collectionId}/webhooks`, data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['collection', variables.collectionId] });
      queryClient.invalidateQueries({ queryKey: ['collections'] });

      toast({
        title: 'Web Request Added',
        description: 'The web request has been added to your collection.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to create web request';
      toast({
        title: 'Failed to Create Web Request',
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
  const { toast } = useToast();

  return useMutation<Webhook, Error, { webhookId: string; data: UpdateWebhookRequest }>({
    mutationFn: async ({ webhookId, data }) => {
      const response = await api.put(`/api/collections/webhooks/${webhookId}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['collection'] });

      toast({
        title: 'Web Request Updated',
        description: 'The web request has been updated successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to update web request';
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
  const { toast } = useToast();

  return useMutation<void, Error, string>({
    mutationFn: async (webhookId: string) => {
      await api.delete(`/api/collections/webhooks/${webhookId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['collection'] });

      toast({
        title: 'Web Request Deleted',
        description: 'The web request has been removed successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to delete web request';
      toast({
        title: 'Delete Failed',
        description: message,
        variant: 'destructive',
      });
    },
  });
};
