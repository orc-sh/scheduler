/**
 * Subscription types for plan management
 */

export interface Subscription {
  id: string;
  account_id: string;
  chargebee_subscription_id: string;
  chargebee_customer_id: string;
  plan_id: string;
  status: string;
  current_term_start: string | null;
  current_term_end: string | null;
  trial_end: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateSubscriptionRequest {
  plan_id: string;
}

export interface CancelSubscriptionRequest {
  cancel_reason?: string;
}

export type PlanId =
  | 'free-plan-INR-Monthly'
  | 'free-plan-INR-Yearly'
  | 'pro-plan-INR-Monthly'
  | 'pro-plan-INR-Yearly';

export const PLAN_IDS = {
  FREE: 'free-plan-INR-Monthly' as const,
  FREE_YEARLY: 'free-plan-INR-Yearly' as const,
  PRO: 'pro-plan-INR-Monthly' as const,
  PRO_YEARLY: 'pro-plan-INR-Yearly' as const,
} as const;
