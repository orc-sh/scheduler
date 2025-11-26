/**
 * Custom hook for Load Test API operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';
import type {
  CreateLoadTestConfigurationRequest,
  LoadTestConfiguration,
  LoadTestConfigurationWithRuns,
  LoadTestReport,
  LoadTestReportWithResults,
  LoadTestRun,
  LoadTestRunWithReports,
  PaginatedLoadTestConfigurationResponse,
  UpdateLoadTestConfigurationRequest,
} from '@/types/load-test.types';

/**
 * Fetch all load test configurations with pagination
 */
export const useLoadTestConfigurations = (
  page: number = 1,
  pageSize: number = 10,
  projectId?: string
) => {
  return useQuery<PaginatedLoadTestConfigurationResponse, Error>({
    queryKey: ['load-test-configurations', page, pageSize, projectId],
    queryFn: async () => {
      const params: any = { page, page_size: pageSize };
      if (projectId) params.project_id = projectId;
      const response = await api.get('/api/load-tests/configurations', { params });
      return response.data;
    },
  });
};

/**
 * Fetch a single load test configuration by ID
 */
export const useLoadTestConfiguration = (configId: string) => {
  return useQuery<LoadTestConfigurationWithRuns, Error>({
    queryKey: ['load-test-configuration', configId],
    queryFn: async () => {
      const response = await api.get(`/api/load-tests/configurations/${configId}`);
      return response.data;
    },
    enabled: !!configId,
  });
};

/**
 * Fetch all runs for a configuration
 */
export const useLoadTestRuns = (configId: string) => {
  return useQuery<LoadTestRun[], Error>({
    queryKey: ['load-test-runs', configId],
    queryFn: async () => {
      const response = await api.get(`/api/load-tests/configurations/${configId}/runs`);
      return response.data;
    },
    enabled: !!configId,
  });
};

/**
 * Fetch a single load test run by ID
 */
export const useLoadTestRun = (runId: string, includeResults: boolean = false) => {
  return useQuery<LoadTestRunWithReports, Error>({
    queryKey: ['load-test-run', runId, includeResults],
    queryFn: async () => {
      const params: any = {};
      if (includeResults) {
        params.include_results = true;
      }
      const response = await api.get(`/api/load-tests/runs/${runId}`, { params });
      return response.data;
    },
    enabled: !!runId,
  });
};

/**
 * Fetch all reports for a run
 */
export const useLoadTestReports = (runId: string) => {
  return useQuery<LoadTestReport[], Error>({
    queryKey: ['load-test-reports', runId],
    queryFn: async () => {
      const response = await api.get(`/api/load-tests/runs/${runId}/reports`);
      return response.data;
    },
    enabled: !!runId,
  });
};

/**
 * Fetch a single report with results
 */
export const useLoadTestReport = (reportId: string, page: number = 1, pageSize: number = 50) => {
  return useQuery<LoadTestReportWithResults, Error>({
    queryKey: ['load-test-report', reportId, page, pageSize],
    queryFn: async () => {
      const response = await api.get(`/api/load-tests/reports/${reportId}`, {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
    enabled: !!reportId,
  });
};

/**
 * Create a new load test configuration
 */
export const useCreateLoadTestConfiguration = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<LoadTestConfiguration, Error, CreateLoadTestConfigurationRequest>({
    mutationFn: async (data: CreateLoadTestConfigurationRequest) => {
      const response = await api.post('/api/load-tests/configurations', data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate configurations query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['load-test-configurations'] });

      toast({
        title: 'Benchmark Configuration Created! 🚀',
        description: 'Your benchmark configuration has been created successfully.',
      });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message =
        error.response?.data?.detail || error.message || 'Failed to create benchmark configuration';
      toast({
        title: 'Failed to Create Benchmark Configuration',
        description: message,
        variant: 'destructive',
      });
    },
  });
};

/**
 * Update a load test configuration
 */
export const useUpdateLoadTestConfiguration = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<
    LoadTestConfiguration,
    Error,
    { id: string; data: UpdateLoadTestConfigurationRequest }
  >({
    mutationFn: async ({ id, data }) => {
      const response = await api.put(`/api/load-tests/configurations/${id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['load-test-configurations'] });
      queryClient.invalidateQueries({ queryKey: ['load-test-configuration', data.id] });

      toast({
        title: 'Benchmark Configuration Updated',
        description: 'Your benchmark configuration has been updated successfully.',
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
 * Delete a load test configuration
 */
export const useDeleteLoadTestConfiguration = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<void, Error, string>({
    mutationFn: async (configId: string) => {
      await api.delete(`/api/load-tests/configurations/${configId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['load-test-configurations'] });

      toast({
        title: 'Benchmark Configuration Deleted',
        description: 'The benchmark configuration has been removed successfully.',
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
 * Create a new load test run from a configuration
 */
export const useCreateLoadTestRun = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<LoadTestRun, Error, string>({
    mutationFn: async (configId: string) => {
      const response = await api.post(`/api/load-tests/configurations/${configId}/runs`);
      return response.data;
    },
    onSuccess: (data, configId) => {
      queryClient.invalidateQueries({ queryKey: ['load-test-configurations'] });
      queryClient.invalidateQueries({ queryKey: ['load-test-configuration', configId] });
      queryClient.invalidateQueries({ queryKey: ['load-test-runs', configId] });
      queryClient.invalidateQueries({ queryKey: ['load-test-run', data.id] });

      toast({
        title: 'Benchmark Started! 🚀',
        description: 'Your benchmark run has been created and started.',
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
 * Manually trigger a load test run
 */
export const useRunLoadTest = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<LoadTestRun, Error, string>({
    mutationFn: async (runId: string) => {
      const response = await api.post(`/api/load-tests/runs/${runId}/run`);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['load-test-runs'] });
      queryClient.invalidateQueries({ queryKey: ['load-test-run', data.id] });
      queryClient.invalidateQueries({ queryKey: ['load-test-reports', data.id] });

      toast({
        title: 'Benchmark Started',
        description: `Benchmark run is now running.`,
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
 * Delete a load test run
 */
export const useDeleteLoadTestRun = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation<void, Error, string>({
    mutationFn: async (runId: string) => {
      await api.delete(`/api/load-tests/runs/${runId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['load-test-runs'] });
      queryClient.invalidateQueries({ queryKey: ['load-test-configurations'] });

      toast({
        title: 'Benchmark Run Deleted',
        description: 'The benchmark run has been removed successfully.',
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
