import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCollections } from '@/hooks/use-load-tests';
import { useProjects } from '@/hooks/use-projects';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Plus, Gauge, ChevronLeft, ChevronRight, Clock, Zap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const LoadTestsPage = () => {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Fetch projects to get the first one for creating collections
  const { data: projectsData } = useProjects(1, 1);
  const firstProject = projectsData?.data?.[0];

  // Fetch load test configurations
  const { data: configsData, isLoading, isError } = useCollections(currentPage, pageSize);

  const configurations = configsData?.data || [];
  const pagination = configsData?.pagination;

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto max-w-6xl">
        <FadeIn>
          {/* Header */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Collections</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Create collections of web requests and run load tests
              </p>
            </div>
            <Button onClick={() => navigate('/load-tests/new')} disabled={!firstProject}>
              <Plus className="mr-2 h-4 w-4" />
              New Collection
            </Button>
          </div>

          {/* Error State */}
          {isError && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive">
              Failed to load collections. Please try again.
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
          {!isLoading && configurations.length === 0 && currentPage === 1 && (
            <div className="mt-16 flex flex-col items-center justify-center rounded-lg border border-dashed border-muted-foreground/25 bg-muted/5 p-16 text-center">
              <div className="rounded-full bg-muted/50 p-4">
                <Gauge className="h-10 w-10 text-muted-foreground/50" />
              </div>
              <h2 className="mt-6 text-xl font-semibold">No collections yet</h2>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                Create a collection to group web requests together. You can then run load tests with
                different execution parameters.
              </p>
              <Button
                onClick={() => navigate('/load-tests/new')}
                className="mt-6"
                size="lg"
                disabled={!firstProject}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Collection
              </Button>
            </div>
          )}

          {/* Configurations List */}
          {!isLoading && configurations.length > 0 && (
            <>
              <div className="space-y-3">
                {configurations.map((config) => (
                  <Card
                    key={config.id}
                    className="group rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm cursor-pointer"
                    onClick={() => navigate(`/load-tests/${config.id}`)}
                  >
                    <CardContent className="flex items-center justify-between gap-6 p-4">
                      {/* Left Side - Information */}
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                          <Gauge className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-sm text-foreground truncate">
                              {config.name || 'Unnamed Collection'}
                            </h3>
                            {config.webhooks && config.webhooks.length > 0 && (
                              <Badge variant="outline" className="text-xs">
                                {config.webhooks.length} request
                                {config.webhooks.length !== 1 ? 's' : ''}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1.5">
                              <Clock className="h-3 w-3" />
                              <span>
                                {formatDistanceToNow(new Date(config.created_at), {
                                  addSuffix: true,
                                })}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span>
                                {config.webhooks?.length || 0} web request
                                {(config.webhooks?.length || 0) !== 1 ? 's' : ''}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Pagination */}
              {!isLoading && configurations.length > 0 && (
                <div className="mt-6 flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Page {pagination?.current_page || currentPage} • {configurations.length} item
                    {configurations.length !== 1 ? 's' : ''}
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
                      disabled={configurations.length < pageSize || !pagination?.has_next}
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

export default LoadTestsPage;
