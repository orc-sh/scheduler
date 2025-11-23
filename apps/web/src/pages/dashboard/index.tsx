import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWebhooks, useUpdateWebhook } from '@/hooks/use-webhooks';
import { useCurrentUser } from '@/hooks/use-auth';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Plus,
  Clock,
  ExternalLink,
  RefreshCw,
  CalendarClock,
  Webhook as WebhookIcon,
  ChevronLeft,
  ChevronRight,
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

  // Format HTTP method with color
  const getMethodBadge = (method: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      GET: 'secondary',
      POST: 'default',
      PUT: 'outline',
      PATCH: 'outline',
      DELETE: 'destructive',
    };
    return <Badge variant={variants[method] || 'outline'}>{method}</Badge>;
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
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto max-w-7xl">
        <FadeIn>
          {/* Header */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Webhooks</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {isLoading
                  ? 'Loading...'
                  : `${webhooks.length} webhook${webhooks.length !== 1 ? 's' : ''}`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isLoading}
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button onClick={() => navigate('/add-new')} className="gap-2">
                <Plus className="h-4 w-4" />
                Create Webhook
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
                <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
                  <Skeleton className="h-12 w-12 rounded" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                  <Skeleton className="h-8 w-20" />
                </div>
              ))}
            </div>
          )}

          {/* Webhooks Table */}
          {!isLoading && webhooks.length > 0 && (
            <div className="rounded-lg border border-border/50 bg-card shadow-sm">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="font-semibold">Name</TableHead>
                    <TableHead className="font-semibold">Method</TableHead>
                    <TableHead className="font-semibold">Endpoint</TableHead>
                    <TableHead className="font-semibold">Schedule</TableHead>
                    <TableHead className="font-semibold">Status</TableHead>
                    <TableHead className="font-semibold">Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {webhooks.map((webhook) => (
                    <TableRow
                      key={webhook.id}
                      className="group cursor-pointer hover:bg-accent/50 transition-colors"
                      onClick={() => navigate(`/webhooks/${webhook.id}`)}
                    >
                      <TableCell className="font-medium">
                        {webhook.job?.name || 'Unnamed Job'}
                      </TableCell>
                      <TableCell className="font-mono">{getMethodBadge(webhook.method)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <code className="max-w-md truncate rounded bg-muted px-2 py-1 text-xs font-mono">
                            {webhook.url}
                          </code>
                          <a
                            href={webhook.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="opacity-0 transition-opacity group-hover:opacity-100"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                          </a>
                        </div>
                        {webhook.headers && Object.keys(webhook.headers).length > 0 && (
                          <div className="mt-1 text-xs text-muted-foreground">
                            {Object.keys(webhook.headers).length} header(s)
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-sm">
                          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="font-mono text-xs text-muted-foreground">
                            {webhook.job?.schedule || 'N/A'}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div
                          className="flex items-center gap-2"
                          onClick={(e) => e.stopPropagation()}
                        >
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
                          <span className="text-xs text-muted-foreground">
                            {webhook.job?.enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(webhook.created_at), { addSuffix: true })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
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
  );
};

export default DashboardPage;
