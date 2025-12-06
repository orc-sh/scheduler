import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWebhooks, useUpdateWebhook } from '@/hooks/use-webhooks';
import { useSubscriptions } from '@/hooks/use-subscriptions';
import { getJobLimit } from '@/constants/limits';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { describeCronExpression } from '@/lib/cron-utils';
import { cn } from '@/lib/utils';
import {
  Plus,
  Clock,
  ExternalLink,
  CalendarClock,
  Webhook as WebhookIcon,
  ChevronLeft,
  ChevronRight,
  Globe,
  Hammer,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const ITEMS_PER_PAGE = 10;

const SchedulesPage = () => {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const updateWebhook = useUpdateWebhook();

  // Calculate offset for pagination
  const offset = (currentPage - 1) * ITEMS_PER_PAGE;

  // Fetch webhooks with pagination
  const { data: webhooks = [], isLoading, isError } = useWebhooks(ITEMS_PER_PAGE, offset);
  // Fetch all webhooks to get accurate job count (with high limit)
  const { data: allWebhooks = [] } = useWebhooks(1000, 0);
  const { data: subscriptions } = useSubscriptions();

  // Calculate job limits based on subscription plan
  const jobLimitInfo = useMemo(() => {
    const subscription = subscriptions?.[0]; // Get first subscription (user typically has one)
    const planId = subscription?.plan_id || null;
    const limit = getJobLimit(planId);

    // Count unique jobs from all webhooks (each webhook has a job)
    // Using allWebhooks to get accurate count across all pages
    const uniqueJobIds = new Set(allWebhooks.map((w) => w.job_id).filter(Boolean));
    const currentCount = uniqueJobIds.size;

    return {
      currentCount,
      limit,
    };
  }, [subscriptions, allWebhooks]);

  // Handle toggle enable/disable
  const handleToggleEnabled = async (
    webhookId: string,
    newEnabled: boolean,
    webhookName: string
  ) => {
    try {
      await updateWebhook.mutateAsync({
        id: webhookId,
        data: {
          job: {
            enabled: newEnabled,
          },
        },
      });
      // The hook's onSuccess will show a toast, but we could add a more specific one here if needed
    } catch (error) {
      // Error is handled by the hook's onError
      console.error('Failed to toggle webhook status:', error);
    }
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-6xl">
          <FadeIn>
            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h1 className="text-3xl font-bold tracking-tight">Webhook Schedules</h1>
                    {jobLimitInfo && (
                      <Badge variant="secondary" className="text-xs font-normal">
                        {jobLimitInfo.currentCount} of {jobLimitInfo.limit}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Use cron expressions to trigger your webhooks on schedule.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => navigate('/cron-builder')}
                  className="gap-2"
                >
                  <Hammer className="h-4 w-4" />
                  Expression Builder
                </Button>
                <Button size="sm" onClick={() => navigate('/schedules/new')} className="w-20 gap-2">
                  Create
                </Button>
              </div>
            </div>

            {/* Error State */}
            {isError && (
              <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
                Failed to load webhooks. Please try again.
              </div>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <Card key={i} className="rounded-xl border-border/50">
                    <CardContent className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <Skeleton className="h-10 w-10 rounded" />
                        <div className="flex-1 space-y-2 min-w-0">
                          <Skeleton className="h-4 w-48" />
                          <Skeleton className="h-3 w-64" />
                        </div>
                      </div>
                      <Skeleton className="h-6 w-11 rounded-full" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {!isLoading && webhooks.length === 0 && (
              <div className="mt-16 flex flex-col items-center justify-center rounded-lg border border-dashed border-muted-foreground/25 bg-muted/5 p-16 text-center">
                <div className="rounded-full bg-muted/50 p-4">
                  <WebhookIcon className="h-10 w-10 text-muted-foreground/50" />
                </div>
                <h2 className="mt-6 text-xl font-semibold">No webhooks yet</h2>
                <p className="mt-2 max-w-md text-sm text-muted-foreground">
                  Get started by creating your first scheduled webhook. Configure endpoints, set
                  schedules, and automate your workflows.
                </p>
                <Button onClick={() => navigate('/schedules/new')} className="mt-6" size="lg">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Webhook
                </Button>
                <div className="mt-8 flex items-center gap-6 text-xs text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>Cron scheduling</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CalendarClock className="h-4 w-4" />
                    <span>Multiple timezones</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <WebhookIcon className="h-4 w-4" />
                    <span>REST endpoints</span>
                  </div>
                </div>
              </div>
            )}

            {/* Webhooks List */}
            {!isLoading && webhooks.length > 0 && (
              <>
                <div className="space-y-3">
                  {webhooks.map((webhook) => (
                    <Card
                      key={webhook.id}
                      className="group rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm cursor-pointer"
                      onClick={() => navigate(`/schedules/${webhook.id}`)}
                    >
                      <CardContent className="flex items-center justify-between gap-6 p-4">
                        {/* Left Side - Information */}
                        <div className="flex items-center gap-4 flex-1 min-w-0">
                          <div
                            className={cn(
                              'flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg',
                              webhook.job?.enabled ? 'bg-primary/10' : 'bg-muted/50'
                            )}
                          >
                            <WebhookIcon
                              className={cn(
                                'h-5 w-5',
                                webhook.job?.enabled ? 'text-primary' : 'text-muted-foreground'
                              )}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold text-sm text-foreground truncate">
                                {webhook.job?.name || 'Unnamed Job'}
                              </h3>
                              <Badge variant="outline" className="font-mono text-xs">
                                {webhook.method}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                              <div className="flex items-center gap-1.5 min-w-0">
                                <Globe className="h-3 w-3 flex-shrink-0" />
                                <code className="truncate font-mono text-xs">{webhook.url}</code>
                                <a
                                  href={webhook.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-all hover:text-foreground group-hover:opacity-100"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              </div>
                              {webhook.headers && Object.keys(webhook.headers).length > 0 && (
                                <div className="flex items-center gap-1.5">
                                  <span>
                                    {Object.keys(webhook.headers).length} header
                                    {Object.keys(webhook.headers).length !== 1 ? 's' : ''}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Right Side - Schedule, Time and Toggle */}
                        <div
                          className="flex items-center gap-4 flex-shrink-0"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {webhook.job?.schedule && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                  <CalendarClock className="h-3 w-3" />
                                  <span className="truncate max-w-[200px]">
                                    {(() => {
                                      const description = describeCronExpression(
                                        webhook.job.schedule
                                      );
                                      return description.isValid
                                        ? description.description
                                        : webhook.job.schedule;
                                    })()}
                                  </span>
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <div className="space-y-1">
                                  <p className="text-xs font-medium">Schedule</p>
                                  <code className="text-xs font-mono">{webhook.job.schedule}</code>
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          )}
                          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>
                              {formatDistanceToNow(new Date(webhook.created_at), {
                                addSuffix: true,
                              })}
                            </span>
                          </div>
                          <Switch
                            checked={webhook.job?.enabled ?? false}
                            onCheckedChange={(checked) =>
                              handleToggleEnabled(
                                webhook.id,
                                checked,
                                webhook.job?.name || 'Webhook'
                              )
                            }
                            disabled={updateWebhook.isPending}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Pagination */}
                {!isLoading && webhooks.length > 0 && (
                  <div className="mt-6 flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Page {currentPage} • {webhooks.length} item{webhooks.length !== 1 ? 's' : ''}
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => p + 1)}
                        disabled={webhooks.length < ITEMS_PER_PAGE}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </FadeIn>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default SchedulesPage;
