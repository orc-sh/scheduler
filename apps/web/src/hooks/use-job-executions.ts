/**
 * Custom hook for job execution API operations
 */

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type { JobExecution } from '@/types/webhook.types';

/**
 * Fetch job executions for a webhook
 */
export const useJobExecutions = (webhookId: string | undefined) => {
  return useQuery<JobExecution[], Error>({
    queryKey: ['job-executions', webhookId],
    queryFn: async () => {
      if (!webhookId) {
        throw new Error('Webhook ID is required');
      }
      const response = await api.get(`/api/schedules/${webhookId}/executions`);
      return response.data;
    },
    enabled: !!webhookId,
  });
};
