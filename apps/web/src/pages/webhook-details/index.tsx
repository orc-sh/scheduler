import { useParams, useNavigate } from 'react-router-dom';
import { useWebhook, useDeleteWebhook, useUpdateWebhook } from '@/hooks/use-webhooks';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  ArrowLeft,
  Pencil,
  Trash2,
  ExternalLink,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
  Play,
  AlertCircle,
  Timer,
} from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { formatDistanceToNow, format } from 'date-fns';
import { useState, useMemo } from 'react';
import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import { CartesianGrid, XAxis, YAxis, Bar, BarChart, Cell } from 'recharts';

// Dummy execution logs data
const generateDummyExecutions = () => {
  const statuses = ['success', 'error', 'timeout'];
  const statusCodes = [200, 201, 400, 404, 500, 502, 504];

  return Array.from({ length: 15 }, (_, i) => {
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const statusCode = statusCodes[Math.floor(Math.random() * statusCodes.length)];
    const isSuccess = statusCode >= 200 && statusCode < 300;
    const timestamp = new Date(Date.now() - i * 3600000 - Math.random() * 3600000);

    return {
      id: `exec-${i + 1}`,
      timestamp,
      status: isSuccess ? 'success' : status,
      statusCode,
      duration: Math.floor(Math.random() * 2000) + 100,
      response: isSuccess
        ? {
            status: statusCode,
            body: JSON.stringify(
              {
                message: 'Request processed successfully',
                data: { id: Math.random().toString(36).substring(7) },
              },
              null,
              2
            ),
            headers: {
              'content-type': 'application/json',
              'x-request-id': Math.random().toString(36).substring(7),
            },
          }
        : {
            status: statusCode,
            body: JSON.stringify(
              {
                error: statusCode >= 500 ? 'Internal server error' : 'Bad request',
                message: 'Request failed',
              },
              null,
              2
            ),
            headers: {
              'content-type': 'application/json',
            },
          },
    };
  }).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

const WebhookDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: webhook, isLoading, isError } = useWebhook(id!);
  const deleteWebhook = useDeleteWebhook();
  const updateWebhook = useUpdateWebhook();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [expandedExecution, setExpandedExecution] = useState<string | null>(null);
  const [executions] = useState(generateDummyExecutions());

  // Handle toggle enable/disable
  const handleToggleEnabled = async (newEnabled: boolean) => {
    if (!id) return;
    try {
      await updateWebhook.mutateAsync({
        id,
        data: {
          job: {
            enabled: newEnabled,
          },
        } as any,
      });
    } catch (error) {
      console.error('Failed to toggle webhook status:', error);
    }
  };

  // Prepare chart data - one bar per execution
  const chartData = useMemo(() => {
    return executions.map((exec, index) => ({
      name: `#${executions.length - index}`,
      duration: exec.duration,
      status: exec.statusCode >= 200 && exec.statusCode < 300 ? 'success' : 'error',
      statusCode: exec.statusCode,
      timestamp: format(exec.timestamp, 'MMM dd, HH:mm:ss'),
    }));
  }, [executions]);

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    const total = executions.length;
    const success = executions.filter((e) => e.statusCode >= 200 && e.statusCode < 300).length;
    const error = total - success;
    const avgDuration = Math.round(executions.reduce((sum, e) => sum + e.duration, 0) / total);
    const successRate = total > 0 ? Math.round((success / total) * 100) : 0;

    return { total, success, error, avgDuration, successRate };
  }, [executions]);

  // Format HTTP method with normal colors
  const getMethodBadge = (method: string) => {
    return (
      <Badge
        variant="outline"
        className="font-mono text-xs bg-muted/30 text-foreground border-border"
      >
        {method}
      </Badge>
    );
  };

  const getStatusBadge = (_status: string, statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) {
      return (
        <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    } else if (statusCode >= 400 && statusCode < 500) {
      return (
        <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
          <AlertCircle className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    } else {
      return (
        <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
          <XCircle className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    }
  };

  const handleDelete = () => {
    if (id) {
      deleteWebhook.mutate(id, {
        onSuccess: () => {
          navigate('/dashboard');
        },
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-6 pl-24">
        <div className="container mx-auto space-y-6 max-w-7xl">
          <Skeleton className="h-10 w-32 mb-4" />
          <Skeleton className="h-16 w-full" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !webhook) {
    return (
      <div className="min-h-screen bg-background p-6 pl-24">
        <div className="container mx-auto max-w-4xl">
          <FadeIn>
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-6 text-center">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Webhook Not Found</h2>
              <p className="text-sm text-muted-foreground mb-4">
                The webhook you're looking for could not be found.
              </p>
              <Button onClick={() => navigate('/dashboard')}>Return to Dashboard</Button>
            </div>
          </FadeIn>
        </div>
      </div>
    );
  }

  const job = webhook.job;

  return (
    <div className="min-h-screen bg-background p-6 pl-24">
      <div className="container mx-auto space-y-8 max-w-7xl">
        {/* Header */}
        <FadeIn>
          <div className="space-y-4">
            {/* Navigation Breadcrumb */}
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      navigate('/dashboard');
                    }}
                    className="flex items-center gap-1.5"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    Dashboard
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage className="truncate">{job?.name || 'Webhook'}</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>

            {/* Title and Actions */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                  {job?.name || 'Unnamed Webhook'}
                </h1>
                <p className="text-sm text-muted-foreground mt-1 truncate">{webhook.url}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="outline"
                  onClick={() => navigate(`/edit/${webhook.id}`)}
                  size="sm"
                  className="h-9 hover:bg-transparent hover:text-muted-foreground hover:border-muted-foreground/50"
                >
                  <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setDeleteDialogOpen(true)}
                  size="sm"
                  className="h-9 hover:bg-transparent hover:border-destructive/50 hover:text-destructive/70"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </FadeIn>

        {/* Execution Overview Chart */}
        <FadeIn delay={0.1}>
          <Card className="border">
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Execution Overview</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Success rate: {summaryStats.successRate}% • Avg response:{' '}
                    {summaryStats.avgDuration}ms
                  </p>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="h-2 w-2 rounded-full bg-emerald-500" />
                    <span className="text-muted-foreground">Success ({summaryStats.success})</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="h-2 w-2 rounded-full bg-red-500" />
                    <span className="text-muted-foreground">Error ({summaryStats.error})</span>
                  </div>
                </div>
              </div>
              <ChartContainer
                config={{
                  success: {
                    label: 'Success',
                    color: 'hsl(160, 84%, 39%)',
                  },
                  error: {
                    label: 'Error',
                    color: 'hsl(0, 84%, 60%)',
                  },
                }}
                className="h-[300px] w-full"
              >
                <BarChart
                  data={chartData}
                  barCategoryGap="20%"
                  margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    width={50}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    label={{
                      value: 'ms',
                      angle: -90,
                      position: 'insideLeft',
                      style: { textAnchor: 'middle', fontSize: 11 },
                    }}
                  />
                  <ChartTooltip
                    cursor={false}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="rounded-lg border bg-background p-2.5 shadow-sm">
                            <div className="grid gap-1.5">
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Status</span>
                                <Badge
                                  variant="outline"
                                  className={
                                    data.status === 'success'
                                      ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20 text-[10px] h-5 px-1.5'
                                      : 'bg-red-500/10 text-red-600 border-red-500/20 text-[10px] h-5 px-1.5'
                                  }
                                >
                                  {data.statusCode}
                                </Badge>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Duration</span>
                                <span className="text-[10px] font-medium">{data.duration}ms</span>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Time</span>
                                <span className="text-[10px] font-medium">{data.timestamp}</span>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="duration" radius={[2, 2, 0, 0]} maxBarSize={24}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.status === 'success' ? 'hsl(160, 84%, 39%)' : 'hsl(0, 84%, 60%)'
                        }
                        style={{ opacity: 0.9 }}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>
        </FadeIn>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Execution Logs */}
          <div className="lg:col-span-2 space-y-4">
            {/* Execution Logs */}
            <FadeIn delay={0.3}>
              <Card className="border">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-foreground">Execution Logs</h3>
                    <Badge variant="outline" className="text-xs">
                      {executions.length} executions
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    {executions.map((execution) => (
                      <div
                        key={execution.id}
                        className="border rounded-md hover:bg-muted/30 transition-colors"
                      >
                        <button
                          onClick={() =>
                            setExpandedExecution(
                              expandedExecution === execution.id ? null : execution.id
                            )
                          }
                          className="w-full p-3 flex items-center justify-between text-left"
                        >
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            <div className="shrink-0">
                              {expandedExecution === execution.id ? (
                                <ChevronDown className="h-4 w-4 text-muted-foreground" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                              )}
                            </div>
                            <div className="shrink-0">
                              <Play className="h-3.5 w-3.5 text-muted-foreground" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                {getStatusBadge(execution.status, execution.statusCode)}
                                <span className="text-xs text-muted-foreground">
                                  {formatDistanceToNow(execution.timestamp, { addSuffix: true })}
                                </span>
                              </div>
                              <p className="text-xs text-muted-foreground truncate">
                                {execution.timestamp.toLocaleString()}
                              </p>
                            </div>
                            <div className="flex items-center gap-3 shrink-0">
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Timer className="h-3 w-3" />
                                {execution.duration}ms
                              </div>
                            </div>
                          </div>
                        </button>
                        {expandedExecution === execution.id && (
                          <div className="border-t p-4 bg-muted/10 space-y-3">
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-2">
                                Response ({execution.response.status})
                              </p>
                              <div className="rounded-md border bg-background">
                                <div className="border-b p-2 bg-muted/30">
                                  <p className="text-xs font-medium text-foreground">Headers</p>
                                </div>
                                <div className="p-3">
                                  <div className="space-y-1">
                                    {Object.entries(execution.response.headers).map(
                                      ([key, value]) => (
                                        <div key={key} className="flex gap-2 text-xs">
                                          <code className="text-muted-foreground font-mono">
                                            {key}:
                                          </code>
                                          <code className="text-foreground font-mono">{value}</code>
                                        </div>
                                      )
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-2">Body</p>
                              <pre className="text-xs font-mono p-3 rounded-md bg-background border overflow-x-auto">
                                {execution.response.body}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </FadeIn>
          </div>

          {/* Right Column - Status, Configuration & Metadata */}
          <div className="space-y-4">
            {/* Status Component */}
            <FadeIn delay={0.15}>
              <Card className="border">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-foreground mb-0.5">Status</p>
                      <p className="text-[10px] text-muted-foreground">
                        {job?.enabled ? 'Webhook is active' : 'Webhook is disabled'}
                      </p>
                    </div>
                    <Switch
                      checked={job?.enabled ?? false}
                      onCheckedChange={handleToggleEnabled}
                      disabled={updateWebhook.isPending}
                    />
                  </div>
                </CardContent>
              </Card>
            </FadeIn>

            {/* Configuration Details */}
            <FadeIn delay={0.2}>
              <Card className="border">
                <CardContent className="p-5">
                  <h3 className="text-sm font-semibold mb-4 text-foreground">Configuration</h3>
                  <div className="space-y-3">
                    {/* HTTP Method */}
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-muted-foreground">HTTP Method</p>
                      <div>{getMethodBadge(webhook.method)}</div>
                    </div>

                    {/* Schedule */}
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-muted-foreground">Schedule</p>
                      <code className="text-xs font-mono text-foreground">
                        {job?.schedule || 'N/A'}
                      </code>
                    </div>

                    {/* Timezone */}
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-muted-foreground">Timezone</p>
                      <span className="text-xs text-foreground">{job?.timezone || 'N/A'}</span>
                    </div>

                    {/* Webhook URL */}
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs text-muted-foreground shrink-0">Webhook URL</p>
                      <div className="flex flex-row-reverse items-center gap-1.5 flex-1 min-w-0">
                        <a
                          href={webhook.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                        <code className="text-xs font-mono break-all text-foreground">
                          {webhook.url}
                        </code>
                      </div>
                    </div>

                    {/* Content Type */}
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-muted-foreground">Content Type</p>
                      <code className="text-xs font-mono text-foreground">
                        {webhook.content_type}
                      </code>
                    </div>

                    {(webhook.headers && Object.keys(webhook.headers).length > 0) ||
                    (webhook.query_params && Object.keys(webhook.query_params).length > 0) ||
                    webhook.body_template ? (
                      <div className="pt-3 border-t space-y-3">
                        {webhook.headers && Object.keys(webhook.headers).length > 0 && (
                          <div>
                            <p className="text-xs text-muted-foreground mb-2">
                              Headers ({Object.keys(webhook.headers).length})
                            </p>
                            <div className="space-y-1.5">
                              {Object.entries(webhook.headers).map(([key, value]) => (
                                <div key={key} className="flex items-start gap-2 text-xs">
                                  <code className="font-mono text-muted-foreground shrink-0">
                                    {key}:
                                  </code>
                                  <code className="font-mono text-foreground break-all flex-1">
                                    {value}
                                  </code>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {webhook.query_params && Object.keys(webhook.query_params).length > 0 && (
                          <div>
                            <p className="text-xs text-muted-foreground mb-2">
                              Query Parameters ({Object.keys(webhook.query_params).length})
                            </p>
                            <div className="space-y-1.5">
                              {Object.entries(webhook.query_params).map(([key, value]) => (
                                <div key={key} className="flex items-start gap-2 text-xs">
                                  <code className="font-mono text-muted-foreground shrink-0">
                                    {key} =
                                  </code>
                                  <code className="font-mono text-foreground break-all flex-1">
                                    {value}
                                  </code>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {webhook.body_template && (
                          <div>
                            <p className="text-xs text-muted-foreground mb-2">Body Template</p>
                            <pre className="text-xs font-mono p-3 rounded-md bg-muted/20 overflow-x-auto">
                              {webhook.body_template}
                            </pre>
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
            </FadeIn>

            {/* Metadata */}
            <FadeIn delay={0.25}>
              <Card className="border sticky top-6">
                <CardContent className="p-5">
                  <h3 className="text-sm font-semibold mb-4 text-foreground">Metadata</h3>
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Created</p>
                      <p className="text-sm font-medium">
                        {formatDistanceToNow(new Date(webhook.created_at), { addSuffix: true })}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {new Date(webhook.created_at).toLocaleString()}
                      </p>
                    </div>

                    <div className="border-t pt-4">
                      <p className="text-xs text-muted-foreground mb-1">Last Updated</p>
                      <p className="text-sm font-medium">
                        {formatDistanceToNow(new Date(webhook.updated_at), { addSuffix: true })}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {new Date(webhook.updated_at).toLocaleString()}
                      </p>
                    </div>

                    {job?.next_run_at && (
                      <div className="border-t pt-4">
                        <p className="text-xs text-muted-foreground mb-1">Next Run</p>
                        <p className="text-sm font-medium">
                          {formatDistanceToNow(new Date(job.next_run_at), { addSuffix: true })}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {new Date(job.next_run_at).toLocaleString()}
                        </p>
                      </div>
                    )}

                    {job?.last_run_at && (
                      <div className="border-t pt-4">
                        <p className="text-xs text-muted-foreground mb-1">Last Run</p>
                        <p className="text-sm font-medium">
                          {formatDistanceToNow(new Date(job.last_run_at), { addSuffix: true })}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {new Date(job.last_run_at).toLocaleString()}
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </FadeIn>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete webhook?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The webhook will be permanently removed and will stop
              sending scheduled requests.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteWebhook.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default WebhookDetailsPage;
