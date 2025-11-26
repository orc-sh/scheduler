import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import {
  useLoadTestConfiguration,
  useCreateLoadTestRun,
  useDeleteLoadTestConfiguration,
  useUpdateLoadTestConfiguration,
  useLoadTestRun,
  useLoadTestReport,
} from '@/hooks/use-load-tests';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  ArrowLeft,
  Play,
  Trash2,
  Edit,
  MoreVertical,
  CheckCircle2,
  XCircle,
  Zap,
  Timer,
  Clock,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { UpdateLoadTestConfigurationRequest } from '@/types/load-test.types';

const LoadTestDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState<UpdateLoadTestConfigurationRequest>({
    name: '',
    concurrent_users: 10,
    duration_seconds: 60,
    requests_per_second: undefined,
  });
  const pageSize = 50;

  // Fetch configuration with runs
  const {
    data: config,
    isLoading: configLoading,
    isError: configError,
  } = useLoadTestConfiguration(id || '');
  const createRun = useCreateLoadTestRun();
  const deleteConfig = useDeleteLoadTestConfiguration();
  const updateConfig = useUpdateLoadTestConfiguration();

  // Initialize edit form when config loads
  useEffect(() => {
    if (config) {
      setEditFormData({
        name: config.name,
        concurrent_users: config.concurrent_users,
        duration_seconds: config.duration_seconds,
        requests_per_second: undefined, // Not editable for now
      });
    }
  }, [config]);

  // Fetch selected run details with reports and first page of results
  const { data: selectedRun, isLoading: isRunLoading } = useLoadTestRun(selectedRunId || '', true);

  // Get reports from the run (already includes first page of results)
  const reports = selectedRun?.reports || [];

  // Fetch additional results only when paginating (page > 1)
  // For page 1, we use results from the run response (already loaded)
  const { data: paginatedReport, isLoading: isPaginatedReportLoading } = useLoadTestReport(
    selectedReportId && currentPage > 1 ? selectedReportId : '',
    currentPage,
    pageSize
  );

  const runs = config?.runs || [];

  // Get the currently selected report
  const reportFromRun = reports.find((r) => r.id === selectedReportId);

  // If we're on page 1, use results from the run (already loaded)
  // If we're on page 2+, use results from pagination
  const selectedReport = currentPage === 1 ? reportFromRun : paginatedReport || reportFromRun;

  // Get results - from pagination if page > 1, otherwise from the run
  const selectedReportResults =
    currentPage === 1 ? reportFromRun?.results || [] : paginatedReport?.results || [];

  // Auto-select first report when a run is selected and reports are loaded
  useEffect(() => {
    if (selectedRunId && reports && reports.length > 0 && !selectedReportId) {
      setSelectedReportId(reports[0].id);
      setCurrentPage(1); // Reset to first page when selecting new report
    }
  }, [selectedRunId, reports, selectedReportId]);

  const handleCreateRun = async () => {
    if (!id) return;
    try {
      await createRun.mutateAsync(id);
    } catch (error) {
      // Error handled by hook
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await deleteConfig.mutateAsync(id);
      navigate('/load-tests');
    } catch (error) {
      // Error handled by hook
    }
  };

  const handleEdit = () => {
    setIsEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!id) return;
    try {
      await updateConfig.mutateAsync({ id, data: editFormData });
      setIsEditDialogOpen(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<
      string,
      { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }
    > = {
      pending: { variant: 'outline', label: 'Pending' },
      running: { variant: 'default', label: 'Running' },
      completed: { variant: 'secondary', label: 'Completed' },
      failed: { variant: 'destructive', label: 'Failed' },
      cancelled: { variant: 'outline', label: 'Cancelled' },
    };

    const config = variants[status] || variants.pending;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  if (configError) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-6xl">
          <FadeIn>
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
              Failed to load benchmark configuration. Please try again.
            </div>
          </FadeIn>
        </div>
      </div>
    );
  }

  if (configLoading || !config) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-7xl">
          <FadeIn>
            <div className="space-y-4">
              <Skeleton className="h-10 w-64" />
              <Skeleton className="h-96 w-full" />
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
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="icon" onClick={() => navigate('/load-tests')}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-3xl font-bold tracking-tight">{config.name}</h1>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Benchmark Configuration • {runs.length} run{runs.length !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={handleCreateRun}
                disabled={createRun.isPending}
                size="sm"
                variant="outline"
                className="border-border hover:border-primary hover:text-primary"
              >
                <Play className="mr-2 h-4 w-4" />
                Run Test
              </Button>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm" className="h-9 w-9 p-0">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-48 p-1" align="end">
                  <div className="flex flex-col">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="justify-start"
                      onClick={handleEdit}
                    >
                      <Edit className="mr-2 h-4 w-4" />
                      Edit Configuration
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="justify-start text-destructive hover:text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the benchmark
                            configuration and all its runs and reports.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-destructive text-destructive-foreground"
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Configuration Details */}
          <Card className="rounded-xl border-border/50 mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* URL on top */}
                <div>
                  <p className="text-xs text-muted-foreground mb-1">URL</p>
                  <p className="text-sm font-mono break-all">{config.webhook?.url || 'N/A'}</p>
                </div>

                {/* Second row: Threads, Duration, Method */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Concurrent Threads</p>
                    <div className="flex items-center gap-1.5">
                      <Zap className="h-3.5 w-3.5 text-muted-foreground" />
                      <p className="text-sm font-medium">{config.concurrent_users}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Duration</p>
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                      <p className="text-sm font-medium">{config.duration_seconds}s</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">HTTP Method</p>
                    <Badge variant="outline" className="font-mono">
                      {config.webhook?.method || 'N/A'}
                    </Badge>
                  </div>
                </div>

                {/* Advanced Configuration - only show if exists */}
                {(config.webhook?.headers ||
                  config.webhook?.query_params ||
                  config.webhook?.body_template) && (
                  <div className="pt-4 border-t border-border/50 space-y-3">
                    {config.webhook.headers && Object.keys(config.webhook.headers).length > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Headers</p>
                        <div className="bg-muted/50 rounded p-2 space-y-1">
                          {Object.entries(config.webhook.headers).map(([key, value]) => (
                            <div key={key} className="text-xs font-mono">
                              <span className="text-muted-foreground">{key}:</span> {value}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {config.webhook.query_params &&
                      Object.keys(config.webhook.query_params).length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-2">Query Parameters</p>
                          <div className="bg-muted/50 rounded p-2 space-y-1">
                            {Object.entries(config.webhook.query_params).map(([key, value]) => (
                              <div key={key} className="text-xs font-mono">
                                <span className="text-muted-foreground">{key}:</span> {value}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    {config.webhook.body_template && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Request Body</p>
                        <pre className="bg-muted/50 rounded p-2 text-xs font-mono overflow-x-auto max-h-40 overflow-y-auto">
                          {config.webhook.body_template}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Edit Configuration Dialog */}
          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Edit Configuration</DialogTitle>
                <DialogDescription>
                  Update the benchmark configuration settings. Changes will apply to future test
                  runs.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-name">Configuration Name</Label>
                  <Input
                    id="edit-name"
                    value={editFormData.name}
                    onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-concurrent-users">Concurrent Threads</Label>
                    <Input
                      id="edit-concurrent-users"
                      type="number"
                      min="1"
                      max="1000"
                      value={editFormData.concurrent_users}
                      onChange={(e) =>
                        setEditFormData({
                          ...editFormData,
                          concurrent_users: parseInt(e.target.value) || 1,
                        })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-duration">Duration (seconds)</Label>
                    <Input
                      id="edit-duration"
                      type="number"
                      min="1"
                      max="3600"
                      value={editFormData.duration_seconds}
                      onChange={(e) =>
                        setEditFormData({
                          ...editFormData,
                          duration_seconds: parseInt(e.target.value) || 60,
                        })
                      }
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveEdit} disabled={updateConfig.isPending}>
                  {updateConfig.isPending ? 'Saving...' : 'Save Changes'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Animated Two Column Layout: Runs (Left) and Reports + Results (Right) */}
          <div className="flex gap-6 overflow-hidden">
            {/* Left Column: Runs List - Animates from 100% to 30% */}
            <motion.div
              className="space-y-4 flex-shrink-0"
              initial={false}
              animate={{
                width: selectedRunId ? '30%' : '100%',
              }}
              transition={{
                duration: 0.5,
                ease: [0.16, 1, 0.3, 1],
              }}
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Runs</h2>
                <span className="text-sm text-muted-foreground">{runs.length} total</span>
              </div>

              {runs.length === 0 ? (
                <Card className="rounded-xl border-border/50">
                  <CardContent className="p-8 text-center">
                    <p className="text-sm text-muted-foreground">
                      No runs yet. Click "Run Test" to start a benchmark.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3 max-h-[800px] overflow-y-auto">
                  {runs.map((run) => {
                    return (
                      <motion.div
                        key={run.id}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        transition={{ duration: 0.2 }}
                      >
                        <Card
                          className={cn(
                            'rounded-xl border-border/50 cursor-pointer transition-all hover:border-border hover:shadow-sm',
                            selectedRunId === run.id && 'border-primary bg-primary/5'
                          )}
                          onClick={() => {
                            setSelectedRunId(run.id);
                            // Report will be auto-selected via useEffect when reports load
                            setSelectedReportId(null);
                          }}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-4 flex-1">
                                <div className="flex-shrink-0">{getStatusBadge(run.status)}</div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-sm font-medium">
                                      Run {run.id.slice(0, 8)}
                                    </span>
                                    {run.started_at && (
                                      <span className="text-xs text-muted-foreground">
                                        {formatDistanceToNow(new Date(run.started_at), {
                                          addSuffix: true,
                                        })}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </motion.div>

            {/* Right Column: Reports List and Selected Report with Results - Animates from 0% to 70% */}
            <AnimatePresence mode="wait">
              {selectedRunId && (
                <motion.div
                  key={selectedRunId}
                  className="space-y-4 flex-1 min-w-0"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{
                    duration: 0.4,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                >
                  {/* Running State Empty State */}
                  {selectedRun && selectedRun.status === 'running' ? (
                    <Card className="rounded-xl border-border/50">
                      <CardContent className="p-12 text-center">
                        <div className="flex flex-col items-center justify-center gap-4">
                          <div className="relative">
                            <div className="rounded-full bg-primary/10 p-4">
                              <Play className="h-4 w-4 text-primary" />
                            </div>
                            <div className="absolute inset-0 rounded-full bg-primary/20" />
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold mb-1">Benchmark is Running</h3>
                            <p className="text-sm text-muted-foreground max-w-md">
                              The benchmark is currently executing. Reports and metrics will appear
                              here once the run completes.
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <>
                      {/* Reports List */}
                      <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold">Reports</h2>
                        {!isRunLoading && reports && (
                          <span className="text-sm text-muted-foreground">
                            {reports.length} total
                          </span>
                        )}
                      </div>

                      {/* Selected Report Details - Four Metric Cards */}
                      <AnimatePresence mode="wait">
                        {(isRunLoading && selectedRunId) ||
                        (selectedReportId && !selectedReport && currentPage === 1) ? (
                          <div className="grid grid-cols-2 gap-4">
                            {[...Array(4)].map((_, i) => (
                              <Card key={i} className="rounded-xl border-border/50">
                                <CardContent className="p-4">
                                  <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                      <Skeleton className="h-3 w-24 mb-2" />
                                      <Skeleton className="h-8 w-20" />
                                    </div>
                                    <Skeleton className="h-12 w-12 rounded-full" />
                                  </div>
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        ) : selectedReport ? (
                          <motion.div
                            key={selectedReportId}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.3 }}
                            className="grid grid-cols-2 gap-4"
                          >
                            {/* Total Requests Card */}
                            <Card className="rounded-xl border-border/50">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-xs text-muted-foreground mb-1">
                                      Total Requests
                                    </p>
                                    <p className="text-2xl font-bold">
                                      {selectedReport.total_requests.toLocaleString()}
                                    </p>
                                  </div>
                                  <div className="rounded-full bg-primary/10 p-3">
                                    <Zap className="h-5 w-5 text-primary" />
                                  </div>
                                </div>
                              </CardContent>
                            </Card>

                            {/* Successful Requests Card */}
                            <Card className="rounded-xl border-border/50">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-xs text-muted-foreground mb-1">Successful</p>
                                    <p className="text-2xl font-bold text-green-500">
                                      {selectedReport.successful_requests.toLocaleString()}
                                    </p>
                                    {selectedReport.total_requests > 0 && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        {(
                                          (selectedReport.successful_requests /
                                            selectedReport.total_requests) *
                                          100
                                        ).toFixed(1)}
                                        %
                                      </p>
                                    )}
                                  </div>
                                  <div className="rounded-full bg-green-500/10 p-3">
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                  </div>
                                </div>
                              </CardContent>
                            </Card>

                            {/* Failed Requests Card */}
                            <Card className="rounded-xl border-border/50">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-xs text-muted-foreground mb-1">Failed</p>
                                    <p className="text-2xl font-bold text-destructive">
                                      {selectedReport.failed_requests.toLocaleString()}
                                    </p>
                                    {selectedReport.total_requests > 0 && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        {(
                                          (selectedReport.failed_requests /
                                            selectedReport.total_requests) *
                                          100
                                        ).toFixed(1)}
                                        %
                                      </p>
                                    )}
                                  </div>
                                  <div className="rounded-full bg-destructive/10 p-3">
                                    <XCircle className="h-5 w-5 text-destructive" />
                                  </div>
                                </div>
                              </CardContent>
                            </Card>

                            {/* Average Response Time Card */}
                            <Card className="rounded-xl border-border/50">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-xs text-muted-foreground mb-1">
                                      Avg Response Time
                                    </p>
                                    <p className="text-2xl font-bold">
                                      {selectedReport.avg_response_time_ms
                                        ? `${selectedReport.avg_response_time_ms}ms`
                                        : 'N/A'}
                                    </p>
                                    {selectedReport.p95_response_time_ms && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        P95: {selectedReport.p95_response_time_ms}ms
                                      </p>
                                    )}
                                  </div>
                                  <div className="rounded-full bg-blue-500/10 p-3">
                                    <Timer className="h-5 w-5 text-blue-500" />
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          </motion.div>
                        ) : null}
                      </AnimatePresence>

                      {/* Results List */}
                      {selectedReport && selectedRun && selectedRun.status !== 'running' && (
                        <div className="mt-4">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="text-base font-semibold">Results</h3>
                            {!isRunLoading && !isPaginatedReportLoading && (
                              <span className="text-sm text-muted-foreground">
                                {selectedReportResults.length} result
                                {selectedReportResults.length !== 1 ? 's' : ''}
                              </span>
                            )}
                          </div>
                          {isRunLoading || (currentPage > 1 && isPaginatedReportLoading) ? (
                            <div className="space-y-2">
                              {[...Array(5)].map((_, i) => (
                                <Card key={i} className="rounded-xl border-border/50">
                                  <CardContent className="p-3">
                                    <div className="flex items-center justify-between mb-1">
                                      <div className="flex items-center gap-2 flex-1">
                                        <Skeleton className="h-4 w-4 rounded-full" />
                                        <Skeleton className="h-4 w-16" />
                                        <Skeleton className="h-5 w-12" />
                                      </div>
                                      <Skeleton className="h-3 w-16" />
                                    </div>
                                    <Skeleton className="h-3 w-full mt-2" />
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          ) : selectedReportResults.length === 0 ? (
                            <Card className="rounded-xl border-border/50">
                              <CardContent className="p-8 text-center">
                                <p className="text-sm text-muted-foreground">
                                  No results available for this report.
                                </p>
                              </CardContent>
                            </Card>
                          ) : (
                            <div className="space-y-2 max-h-[500px] overflow-y-auto">
                              {selectedReportResults.map((result) => (
                                <motion.div
                                  key={result.id}
                                  initial={{ opacity: 0, x: -10 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ duration: 0.2 }}
                                >
                                  <Card className="rounded-xl border-border/50">
                                    <CardContent className="p-3">
                                      <div className="flex items-center justify-between mb-1">
                                        <div className="flex items-center gap-2">
                                          {result.is_success ? (
                                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                                          ) : (
                                            <XCircle className="h-4 w-4 text-destructive" />
                                          )}
                                          <span className="text-sm font-medium">
                                            {result.method}
                                          </span>
                                          {result.response_status && (
                                            <Badge
                                              variant="outline"
                                              className={cn(
                                                'text-xs',
                                                result.response_status >= 200 &&
                                                  result.response_status < 300
                                                  ? 'border-green-500 text-green-500'
                                                  : result.response_status >= 400
                                                    ? 'border-destructive text-destructive'
                                                    : ''
                                              )}
                                            >
                                              {result.response_status}
                                            </Badge>
                                          )}
                                        </div>
                                        <span className="text-xs text-muted-foreground">
                                          {result.response_time_ms}ms
                                        </span>
                                      </div>
                                      <code className="text-xs text-muted-foreground truncate block">
                                        {result.endpoint_path}
                                      </code>
                                      {result.error_message && (
                                        <div className="mt-2 text-xs text-destructive bg-destructive/10 p-2 rounded">
                                          {result.error_message}
                                        </div>
                                      )}
                                    </CardContent>
                                  </Card>
                                </motion.div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </FadeIn>
      </div>
    </div>
  );
};

export default LoadTestDetailsPage;
