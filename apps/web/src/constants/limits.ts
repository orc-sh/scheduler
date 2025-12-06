/**
 * Creation limits per plan
 * These constants match the backend constants in rate_limiter_service.py
 */

// URL creation limits per plan
export const URL_CREATION_LIMITS = {
  free: 10,
  pro: 10,
} as const;

// Job/schedule creation limits per plan
export const JOB_CREATION_LIMITS = {
  free: 10,
  pro: 100,
} as const;

/**
 * Determine plan type from plan ID
 * Matches the backend logic in rate_limiter_service._get_plan_type
 */
export const getPlanType = (planId: string | null | undefined): 'free' | 'pro' => {
  if (!planId) {
    return 'free';
  }

  const planLower = planId.toLowerCase();
  if (planLower.startsWith('pro')) {
    return 'pro';
  }

  return 'free';
};

/**
 * Get URL creation limit for a plan
 */
export const getUrlLimit = (planId: string | null | undefined): number | null => {
  const planType = getPlanType(planId);
  const limit = URL_CREATION_LIMITS[planType];
  return limit === null ? null : limit;
};

/**
 * Get job creation limit for a plan
 */
export const getJobLimit = (planId: string | null | undefined): number => {
  const planType = getPlanType(planId);
  return JOB_CREATION_LIMITS[planType];
};
