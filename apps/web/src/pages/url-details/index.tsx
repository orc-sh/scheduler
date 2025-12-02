import { useState } from 'react';
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
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';

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
  const hasSelectedLog = !!selectedLogId;

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
              className="mb-4 group rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm"
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

          {/* Animated Layout: Logs List (Left) and Log Details (Right) */}
          <motion.div
            className="grid gap-6 relative"
            initial={false}
            animate={{
              gridTemplateColumns: hasSelectedLog ? '1fr 2fr' : '1fr',
            }}
            transition={{
              duration: 0.4,
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            {/* Left Column: Logs List */}
            <motion.div className="min-w-0" layout>
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
                    <div className="max-h-[calc(100vh-200px)] overflow-y-auto no-scrollbar space-y-2">
                      {logs.map((log) => (
                        <button
                          key={log.id}
                          onClick={() => setSelectedLogId(log.id)}
                          className={`w-full text-left p-4 border border-border/50 rounded-lg transition-colors hover:bg-muted/50 ${
                            selectedLogId === log.id ? 'bg-green-800/10 border-primary' : ''
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-2">
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
                              <p
                                className={cn(
                                  'text-xs text-muted-foreground truncate max-w-[100%]',
                                  hasSelectedLog && 'max-w-[300px]'
                                )}
                              >
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
            </motion.div>

            {/* Right Column: Selected Log Details */}
            <AnimatePresence mode="wait">
              {hasSelectedLog && selectedLog && (
                <motion.div
                  key={selectedLog.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{
                    duration: 0.4,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  className="min-w-0"
                  layout
                >
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
                        <TabsList className="grid w-full grid-cols-3">
                          <TabsTrigger value="headers">Headers</TabsTrigger>
                          <TabsTrigger value="query">Query Params</TabsTrigger>
                          <TabsTrigger value="request">Body</TabsTrigger>
                        </TabsList>

                        <TabsContent value="query" className="mt-4">
                          {selectedLog.query_params &&
                          Object.keys(selectedLog.query_params).length > 0 ? (
                            <div className="space-y-2">
                              {Object.entries(selectedLog.query_params).map(([key, value]) => (
                                <div
                                  key={key}
                                  className="grid grid-cols-3 gap-2 p-2 rounded items-center"
                                >
                                  <p className="text-sm font-semibold text-muted-foreground col-span-1">
                                    {key}
                                  </p>
                                  <div className="flex items-center justify-between gap-2 col-span-2">
                                    <code className="text-xs break-all">{value}</code>
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
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">No query parameters</p>
                          )}
                        </TabsContent>

                        <TabsContent value="headers" className="mt-4">
                          {selectedLog.headers && Object.keys(selectedLog.headers).length > 0 ? (
                            <div className="space-y-2">
                              {Object.entries(selectedLog.headers).map(([key, value]) => (
                                <div
                                  key={key}
                                  className="grid grid-cols-3 gap-2 p-2 rounded items-center"
                                >
                                  <p className="text-sm font-semibold text-muted-foreground col-span-1">
                                    {key}
                                  </p>
                                  <div className="flex items-center justify-between gap-2 col-span-2">
                                    <code className="text-xs break-all">{value}</code>
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
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">No headers</p>
                          )}
                        </TabsContent>

                        <TabsContent value="request" className="mt-4">
                          {/* Body Section */}
                          <div>
                            <h4 className="text-sm font-semibold mb-2">Request Body</h4>
                            {selectedLog.body ? (
                              <div className="relative">
                                <pre className="max-h-[300px] overflow-auto rounded bg-muted p-4 text-xs">
                                  <code className="language-json">
                                    {(() => {
                                      try {
                                        return JSON.stringify(
                                          JSON.parse(selectedLog.body),
                                          null,
                                          2
                                        );
                                      } catch {
                                        return selectedLog.body;
                                      }
                                    })()}
                                  </code>
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
                              <p className="text-sm text-center text-muted-foreground">No body</p>
                            )}
                          </div>
                        </TabsContent>
                      </Tabs>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

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
