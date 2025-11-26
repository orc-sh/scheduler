import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUrlLogs } from '@/hooks/use-urls';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Copy, Check, Globe, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';
import type { UrlLog } from '@/types/url.types';

const UrlDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 50;

  const { data: urlData, isLoading, isError } = useUrlLogs(id || '', currentPage, pageSize);

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
    if (!status) return 'bg-gray-500';
    if (status >= 200 && status < 300) return 'bg-green-500';
    if (status >= 300 && status < 400) return 'bg-blue-500';
    if (status >= 400 && status < 500) return 'bg-yellow-500';
    return 'bg-red-500';
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

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto max-w-7xl">
        <FadeIn>
          {/* Header */}
          <div className="mb-6 flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold tracking-tight">URL Details</h1>
              {url && (
                <div className="mt-2 flex items-center gap-2">
                  <code className="text-sm text-muted-foreground">{url.path}</code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      const fullPath = `${window.location.origin}${url.path}`;
                      handleCopy(fullPath, url.id);
                    }}
                  >
                    {copiedId === url.id ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* URL Info Card */}
          {url && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  URL Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Path:</span>
                  <code className="text-sm">{url.path}</code>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Unique ID:</span>
                  <code className="text-sm">{url.unique_identifier}</code>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Created:</span>
                  <span className="text-sm">
                    {formatDistanceToNow(new Date(url.created_at), { addSuffix: true })}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Logs:</span>
                  <span className="text-sm">{logs.length}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Two Column Layout: Logs List (Left) and Log Details (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Logs List */}
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Request Logs ({logs.length})
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
                    <div className="max-h-[calc(100vh-400px)] overflow-y-auto">
                      {logs.map((log) => (
                        <button
                          key={log.id}
                          onClick={() => setSelectedLogId(log.id)}
                          className={`w-full text-left p-4 border-b border-border/50 transition-colors hover:bg-muted/50 ${
                            selectedLogId === log.id ? 'bg-muted border-l-4 border-l-primary' : ''
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
                            {log.ip_address && (
                              <span className="text-xs text-muted-foreground truncate max-w-[100px]">
                                {log.ip_address}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(log.created_at), {
                              addSuffix: true,
                            })}
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
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge
                          className={`${getStatusColor(selectedLog.response_status)} text-white`}
                        >
                          {selectedLog.method}
                        </Badge>
                        {selectedLog.response_status && (
                          <Badge variant="outline">{selectedLog.response_status}</Badge>
                        )}
                        <span className="text-sm text-muted-foreground font-normal">
                          {formatDistanceToNow(new Date(selectedLog.created_at), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                      {selectedLog.ip_address && (
                        <span className="text-sm text-muted-foreground font-normal">
                          {selectedLog.ip_address}
                        </span>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
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
        </FadeIn>
      </div>
    </div>
  );
};

export default UrlDetailsPage;
