import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUrls, useCreateUrl } from '@/hooks/use-urls';
import { useProjects, useCreateProject } from '@/hooks/use-projects';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, ExternalLink, Copy, Check, Globe, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from '@/hooks/use-toast';

const UrlsPage = () => {
  const navigate = useNavigate();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Fetch projects to get the first one for creating URLs
  const { data: projectsData } = useProjects(1, 1);
  const firstProject = projectsData?.data?.[0];

  // Fetch URLs
  const { data: urlsData, isLoading, isError } = useUrls(currentPage, pageSize);
  const createUrl = useCreateUrl();
  const createProject = useCreateProject();

  const handleCreateUrl = async () => {
    try {
      let projectId = firstProject?.id;

      // If no project exists, create one first
      if (!projectId) {
        const newProject = await createProject.mutateAsync({ name: 'Default Project' });
        projectId = newProject.id;
      }

      // Create URL with the project ID
      await createUrl.mutateAsync({ project_id: projectId });
    } catch (error) {
      // Error is handled by the hooks
    }
  };

  const handleCopyPath = (path: string, urlId: string) => {
    const fullPath = `${window.location.origin}${path}`;
    navigator.clipboard.writeText(fullPath);
    setCopiedId(urlId);
    toast({
      title: 'Copied!',
      description: 'URL path copied to clipboard',
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  const urls = urlsData?.data || [];
  const pagination = urlsData?.pagination;

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto max-w-6xl">
        <FadeIn>
          {/* Header */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Webhook Endpoints</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Point to these endpoints to receive and log incoming requests.
              </p>
            </div>
            <Button
              onClick={handleCreateUrl}
              disabled={createUrl.isPending || createProject.isPending}
            >
              Create
            </Button>
          </div>

          {/* Error State */}
          {isError && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
              Failed to load URLs. Please try again.
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
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && urls.length === 0 && currentPage === 1 && (
            <div className="mt-16 flex flex-col items-center justify-center rounded-lg border border-dashed border-muted-foreground/25 bg-muted/5 p-16 text-center">
              <div className="rounded-full bg-muted/50 p-4">
                <Globe className="h-10 w-10 text-muted-foreground/50" />
              </div>
              <h2 className="mt-6 text-xl font-semibold">No endpoints yet</h2>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                Create an endpoint to receive and log incoming requests. Similar to webhook.site,
                you can use these endpoints to test and debug webhooks.
              </p>
              <Button
                onClick={handleCreateUrl}
                className="mt-6"
                size="lg"
                disabled={createUrl.isPending || createProject.isPending}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Endpoint
              </Button>
            </div>
          )}

          {/* URLs List */}
          {!isLoading && urls.length > 0 && (
            <>
              <div className="space-y-3">
                {urls.map((url) => (
                  <Card
                    key={url.id}
                    className="group rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm cursor-pointer"
                    onClick={() => navigate(`/endpoints/${url.id}`)}
                  >
                    <CardContent className="flex items-center justify-between gap-6 p-4">
                      {/* Left Side - Information */}
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                          <Globe className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-sm text-foreground truncate">
                              {url.path}
                            </h3>
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
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Pagination */}
              {!isLoading && urls.length > 0 && (
                <div className="mt-6 flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Page {pagination?.current_page || currentPage} • {urls.length} item
                    {urls.length !== 1 ? 's' : ''}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1 || !pagination?.has_previous}
                      className="h-8 w-8 p-0"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => p + 1)}
                      disabled={urls.length < pageSize || !pagination?.has_next}
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
  );
};

export default UrlsPage;
