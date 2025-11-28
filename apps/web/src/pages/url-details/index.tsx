import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUrlLogs, useDeleteUrl } from '@/hooks/use-urls';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  Copy,
  Check,
  Globe,
  Clock,
  Trash2,
  ChevronLeft,
  Send,
  ExternalLink,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';

const UrlDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const pageSize = 50;

  const { data: urlData, isLoading, isError } = useUrlLogs(id || '', currentPage, pageSize);
  const deleteUrl = useDeleteUrl();

  const logs = urlData?.logs || [];
  const selectedLog = logs.find((log) => log.id === selectedLogId) || null;

  // Auto-select first log when logs are loaded
  useEffect(() => {
    if (logs.length > 0 && !selectedLogId) {
      setSelectedLogId(logs[0].id);
    }
  }, [logs, selectedLogId]);

  const handleCopy = (text: string, logId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(logId);
    toast({
      title: 'Copied!',
      description: 'Content copied to clipboard',
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusColor = (status?: number) => {
    if (!status) return 'bg-gray-500 hover:bg-gray-500/80';
    if (status >= 200 && status < 300) return 'bg-green-500 hover:bg-green-500/80';
    if (status >= 300 && status < 400) return 'bg-blue-500 hover:bg-blue-500/80';
    if (status >= 400 && status < 500) return 'bg-yellow-500 hover:bg-yellow-500/80';
    return 'bg-red-500 hover:bg-red-500/80';
  };

  const handleDelete = () => {
    if (id) {
      deleteUrl.mutate(id, {
        onSuccess: () => {
          navigate('/urls');
        },
      });
    }
  };

  if (isError) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-6xl">
          <FadeIn>
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
              Failed to load URL details. Please try again.
            </div>
          </FadeIn>
        </div>
      </div>
    );
  }

  const url = urlData;

  const handleCopyPath = (path: string, urlId: string) => {
    navigator.clipboard.writeText(path);
    setCopiedId(urlId);
    toast({
      title: 'Copied!',
      description: 'Content copied to clipboard',
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto max-w-7xl">
        <FadeIn>
          {/* Header */}
          {url ? (
            <Card
              key={url.id}
              className="mb-4 group rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm cursor-pointer"
              onClick={() => navigate(`/urls/${url.id}`)}
            >
              <CardContent className="flex items-center justify-between gap-6 p-4">
                {/* Left Side - Information */}
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                    <Globe className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-sm text-foreground truncate">{url.path}</h3>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(url.created_at), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <code className="truncate font-mono">{url.unique_identifier}</code>
                        <button
                          className="flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-all hover:text-foreground group-hover:opacity-100"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyPath(url.path, url.id);
                          }}
                        >
                          {copiedId === url.id ? (
                            <Check className="h-3 w-3" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Side - Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      const fullPath = `${window.location.origin}${url.path}`;
                      window.open(fullPath, '_blank');
                    }}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteDialogOpen(true)}
                    className="h-9 hover:bg-transparent hover:bg-red-800/10 hover:border-red-500/50 hover:text-red-500/70"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="shadow-none bg-muted/80 border-border/50 animate-pulse">
              <CardContent className="flex items-center justify-between gap-6 p-4">
                {/* Left Side - Simulated Loading Info */}
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg">
                    <Skeleton className="h-5 w-5 rounded" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Skeleton className="h-4 w-24 rounded" />
                      <Skeleton className="h-3 w-16 rounded" />
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <Skeleton className="h-3 w-32 rounded" />
                      <Skeleton className="h-3 w-5 rounded" />
                    </div>
                  </div>
                </div>
                {/* Right Side - Simulated Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Skeleton className="h-8 w-8 rounded-full" />
                  <Skeleton className="h-8 w-8 rounded-full" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Two Column Layout: Logs List (Left) and Log Details (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Logs List */}
            <div className="lg:col-span-1">
              <Card className="shadow-none bg-transparent border-none">
                <CardHeader className="py-4 px-0">
                  <CardTitle>
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold">Request Logs</p>
                      <span className="text-xs text-muted-foreground">
                        {logs.length} total requests
                      </span>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  {isLoading ? (
                    <div className="space-y-2 p-4">
                      {[...Array(5)].map((_, i) => (
                        <Skeleton key={i} className="h-16 w-full" />
                      ))}
                    </div>
                  ) : logs.length === 0 ? (
                    <div className="py-8 px-4 text-center text-sm text-muted-foreground">
                      No requests logged yet. Send a request to {url?.path} to see logs here.
                    </div>
                  ) : (
                    <div className="max-h-[calc(100vh-400px)] overflow-y-auto space-y-2">
                      {logs.map((log) => (
                        <button
                          key={log.id}
                          onClick={() => setSelectedLogId(log.id)}
                          className={`w-full text-left p-4 border border-border/50 rounded-lg transition-colors hover:bg-muted/50 ${
                            selectedLogId === log.id ? 'bg-green-800/10 border-primary' : ''
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2 mb-2">
                            <div className="flex items-center gap-2">
                              <Badge
                                className={`${getStatusColor(log.response_status)} text-white text-xs`}
                              >
                                {log.method}
                              </Badge>
                              {log.response_status && (
                                <Badge variant="outline" className="text-xs">
                                  {log.response_status}
                                </Badge>
                              )}
                            </div>

                            <div className="flex items-start justify-between gap-2 flex-col text-xs text-muted-foreground">
                              <p className="text-xs text-muted-foreground truncate max-w-[300px]">
                                {log.user_agent ? log.user_agent : 'Unknown'}
                              </p>
                              {formatDistanceToNow(new Date(log.created_at), {
                                addSuffix: true,
                              })}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Right Column: Selected Log Details */}
            <div className="lg:col-span-2">
              {selectedLog ? (
                <Card className="shadow-none bg-transparent border-none">
                  <CardHeader className="py-4 px-0">
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge
                          className={`${getStatusColor(selectedLog.response_status)} text-white`}
                        >
                          {selectedLog.method}
                        </Badge>
                        <span className="text-sm text-muted-foreground font-normal truncate max-w-[300px]">
                          {selectedLog.user_agent ? selectedLog.user_agent : 'Unknown'}
                        </span>
                      </div>
                      <span className="text-sm text-muted-foreground font-normal">
                        {formatDistanceToNow(new Date(selectedLog.created_at), {
                          addSuffix: true,
                        })}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="bg-card rounded-lg p-4 border border-border/50">
                    <Tabs defaultValue="headers" className="w-full">
                      <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="headers">Headers</TabsTrigger>
                        <TabsTrigger value="query">Query</TabsTrigger>
                        <TabsTrigger value="body">Body</TabsTrigger>
                        <TabsTrigger value="response">Response</TabsTrigger>
                      </TabsList>

                      <TabsContent value="headers" className="mt-4">
                        {selectedLog.headers && Object.keys(selectedLog.headers).length > 0 ? (
                          <div className="space-y-2">
                            {Object.entries(selectedLog.headers).map(([key, value]) => (
                              <div
                                key={key}
                                className="flex items-start justify-between gap-2 p-2 rounded bg-muted/30"
                              >
                                <code className="text-xs break-all">
                                  <span className="font-semibold">{key}:</span> {value}
                                </code>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleCopy(`${key}: ${value}`, selectedLog.id)}
                                  className="flex-shrink-0"
                                >
                                  {copiedId === selectedLog.id ? (
                                    <Check className="h-3 w-3" />
                                  ) : (
                                    <Copy className="h-3 w-3" />
                                  )}
                                </Button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">No headers</p>
                        )}
                      </TabsContent>

                      <TabsContent value="query" className="mt-4">
                        {selectedLog.query_params &&
                        Object.keys(selectedLog.query_params).length > 0 ? (
                          <div className="space-y-2">
                            {Object.entries(selectedLog.query_params).map(([key, value]) => (
                              <div
                                key={key}
                                className="flex items-start justify-between gap-2 p-2 rounded bg-muted/30"
                              >
                                <code className="text-xs break-all">
                                  <span className="font-semibold">{key}:</span> {value}
                                </code>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleCopy(`${key}=${value}`, selectedLog.id)}
                                  className="flex-shrink-0"
                                >
                                  {copiedId === selectedLog.id ? (
                                    <Check className="h-3 w-3" />
                                  ) : (
                                    <Copy className="h-3 w-3" />
                                  )}
                                </Button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">No query parameters</p>
                        )}
                      </TabsContent>

                      <TabsContent value="body" className="mt-4">
                        {selectedLog.body ? (
                          <div className="relative">
                            <pre className="max-h-[600px] overflow-auto rounded bg-muted p-4 text-xs">
                              {selectedLog.body}
                            </pre>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="absolute top-2 right-2"
                              onClick={() => handleCopy(selectedLog.body || '', selectedLog.id)}
                            >
                              {copiedId === selectedLog.id ? (
                                <Check className="h-4 w-4" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">No body</p>
                        )}
                      </TabsContent>

                      <TabsContent value="response" className="mt-4">
                        {selectedLog.response_body ? (
                          <div className="relative">
                            <pre className="max-h-[600px] overflow-auto rounded bg-muted p-4 text-xs">
                              {selectedLog.response_body}
                            </pre>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="absolute top-2 right-2"
                              onClick={() =>
                                handleCopy(selectedLog.response_body || '', selectedLog.id)
                              }
                            >
                              {copiedId === selectedLog.id ? (
                                <Check className="h-4 w-4" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">No response</p>
                        )}
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    {logs.length === 0
                      ? 'No logs available. Send a request to see logs here.'
                      : 'Select a log from the list to view details'}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Delete Confirmation Dialog */}
          <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete URL?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. The URL endpoint will be permanently removed and all
                  associated logs will be deleted.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  {deleteUrl.isPending ? 'Deleting...' : 'Delete'}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </FadeIn>
      </div>
    </div>
  );
};

export default UrlDetailsPage;
