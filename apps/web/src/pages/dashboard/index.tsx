import { useState, type JSX } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWebhooks, useUpdateWebhook } from '@/hooks/use-webhooks';
import { useCurrentUser } from '@/hooks/use-auth';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { describeCronExpression } from '@/lib/cron-utils';
import {
  Plus,
  Clock,
  ExternalLink,
  RefreshCw,
  CalendarClock,
  Webhook as WebhookIcon,
  ChevronLeft,
  ChevronRight,
  Globe,
  ArrowDown,
  Send,
  Edit,
  FileEdit,
  Trash2,
  ArrowUp,
  Sparkles,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const ITEMS_PER_PAGE = 10;

const DashboardPage = () => {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const updateWebhook = useUpdateWebhook();

  // Fetch current user data
  useCurrentUser();

  // Calculate offset for pagination
  const offset = (currentPage - 1) * ITEMS_PER_PAGE;

  // Fetch webhooks with pagination
  const { data: webhooks = [], isLoading, isError, refetch } = useWebhooks(ITEMS_PER_PAGE, offset);

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

  // Get HTTP method icon with white color
  const getMethodIcon = (method: string) => {
    const icons: Record<string, JSX.Element> = {
      GET: <p className="text-white text-[10px] font-bold bg-blue-500 rounded-full">GET</p>,
      POST: <p className="text-white text-[10px] font-bold bg-green-500 rounded-full">POST</p>,
      PUT: <p className="text-white text-[10px] font-bold bg-amber-500 rounded-full">PUT</p>,
      PATCH: <p className="text-white text-[10px] font-bold bg-orange-500 rounded-full">PATCH</p>,
      DELETE: <p className="text-white text-[10px] font-bold bg-destructive rounded-full">DEL</p>,
    };
    return (
      icons[method] || (
        <p className="text-white text-[10px] font-bold bg-muted-foreground rounded-full">GET</p>
      )
    );
  };

  // Get HTTP method background color
  const getMethodBgColor = (method: string): string => {
    const colors: Record<string, string> = {
      GET: 'bg-blue-500',
      POST: 'bg-green-500',
      PUT: 'bg-amber-500',
      PATCH: 'bg-orange-500',
      DELETE: 'bg-destructive',
    };
    return colors[method] || 'bg-muted-foreground';
  };

  // Format HTTP method with color
  const getMethodBadge = (method: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      GET: 'secondary',
      POST: 'outline',
      PUT: 'outline',
      PATCH: 'outline',
      DELETE: 'destructive',
    };
    return (
      <Badge
        variant={variants[method] || 'outline'}
        className="text-[10px] px-1.5 py-0.5 font-medium"
      >
        {method}
      </Badge>
    );
  };

  // Empty state
  if (!isLoading && webhooks.length === 0 && currentPage === 1) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-6xl">
          <FadeIn>
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Webhooks</h1>
                <p className="mt-1 text-sm text-muted-foreground">
                  Manage scheduled webhook endpoints
                </p>
              </div>
            </div>

            {/* Empty State */}
            <div className="mt-16 flex flex-col items-center justify-center rounded-lg border border-dashed border-muted-foreground/25 bg-muted/5 p-16 text-center">
              <div className="rounded-full bg-muted/50 p-4">
                <WebhookIcon className="h-10 w-10 text-muted-foreground/50" />
              </div>
              <h2 className="mt-6 text-xl font-semibold">No webhooks yet</h2>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                Get started by creating your first scheduled webhook. Configure endpoints, set
                schedules, and automate your workflows.
              </p>
              <Button onClick={() => navigate('/add-new')} className="mt-6" size="lg">
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
          </FadeIn>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-7xl">
          <FadeIn>
            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Webhook Schedules</h1>
                <p className="mt-1 text-sm text-muted-foreground">Manage your webhook schedules</p>
              </div>
              <div className="flex items-center gap-3">
                <Button onClick={() => navigate('/add-new')} className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Schedule
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

            {/* Webhooks Cards - Pill Structure */}
            {!isLoading && webhooks.length > 0 && (
              <div className="space-y-3">
                {webhooks.map((webhook) => (
                  <Card
                    key={webhook.id}
                    className="group rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm cursor-pointer"
                    onClick={() => navigate(`/webhooks/${webhook.id}`)}
                  >
                    <CardContent className="flex items-center justify-between gap-6 p-4">
                      {/* HTTP Method Icon - At the start */}
                      <div
                        className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg ${getMethodBgColor(webhook.method)}`}
                      >
                        {getMethodIcon(webhook.method)}
                      </div>

                      {/* Left Side - Information */}
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        {/* Name */}
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold text-sm text-foreground truncate">
                                {webhook.job?.name || 'Unnamed Job'}
                              </h3>
                              <span className="text-xs text-muted-foreground">
                                {formatDistanceToNow(new Date(webhook.created_at), {
                                  addSuffix: true,
                                })}
                              </span>
                            </div>
                            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                              <div className="flex items-center gap-1.5 min-w-0">
                                <Globe className="h-3 w-3 flex-shrink-0" />
                                <code className="truncate font-mono">{webhook.url}</code>
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
                            </div>
                          </div>
                        </div>

                        {/* Additional Metadata */}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-shrink-0">
                          {webhook.headers && Object.keys(webhook.headers).length > 0 && (
                            <span className="hidden lg:inline">
                              {Object.keys(webhook.headers).length} header
                              {Object.keys(webhook.headers).length !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Right Side - Cron Expression and Toggle */}
                      <div className="flex items-center gap-4 flex-shrink-0">
                        {/* Schedule Expression */}
                        <div className="hidden md:flex items-center gap-2 flex-shrink-0 max-w-xs">
                          <Clock className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="text-xs text-muted-foreground truncate cursor-help">
                                {webhook.job?.schedule
                                  ? (() => {
                                      const description = describeCronExpression(
                                        webhook.job.schedule
                                      );
                                      return description.isValid
                                        ? description.description
                                        : webhook.job.schedule;
                                    })()
                                  : 'N/A'}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side="left" className="max-w-xs">
                              <div className="space-y-1">
                                <p className="text-xs font-medium">Schedule</p>
                                <code className="text-xs font-mono">
                                  {webhook.job?.schedule || 'N/A'}
                                </code>
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        </div>

                        {/* Toggle */}
                        <div className="flex-shrink-0" onClick={(e) => e.stopPropagation()}>
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
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

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
          </FadeIn>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default DashboardPage;
