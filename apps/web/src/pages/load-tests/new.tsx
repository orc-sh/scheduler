import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateLoadTestConfiguration } from '@/hooks/use-load-tests';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Gauge, Plus, CircleMinus, Settings2, ChevronDown, Zap, AlertCircle } from 'lucide-react';
import type { CreateLoadTestConfigurationRequest } from '@/types/load-test.types';

// HTTP methods for ToggleGroup
const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] as const;

const NewLoadTestPage = () => {
  const navigate = useNavigate();
  const createConfig = useCreateLoadTestConfiguration();
  const [isAdvancedOpen, setIsAdvancedOpen] = useState<boolean>(false);

  const [formData, setFormData] = useState<Partial<CreateLoadTestConfigurationRequest>>({
    name: '',
    url: '',
    method: 'GET',
    concurrent_users: 10,
    duration_seconds: 60,
    headers: {},
    query_params: {},
    body_template: '',
    content_type: 'application/json',
  });

  const [headerEntries, setHeaderEntries] = useState<Array<{ key: string; value: string }>>([]);
  const [queryParamEntries, setQueryParamEntries] = useState<Array<{ key: string; value: string }>>(
    []
  );

  // Update formData when header/query param entries change
  const updateHeaders = (entries: Array<{ key: string; value: string }>) => {
    const headers: Record<string, string> = {};
    entries.forEach((entry) => {
      if (entry.key.trim()) {
        headers[entry.key.trim()] = entry.value.trim();
      }
    });
    setFormData({ ...formData, headers: Object.keys(headers).length > 0 ? headers : undefined });
  };

  const updateQueryParams = (entries: Array<{ key: string; value: string }>) => {
    const params: Record<string, string> = {};
    entries.forEach((entry) => {
      if (entry.key.trim()) {
        params[entry.key.trim()] = entry.value.trim();
      }
    });
    setFormData({ ...formData, query_params: Object.keys(params).length > 0 ? params : undefined });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.url || !formData.method) {
      return;
    }

    try {
      // Prepare submit data for configuration
      const submitData: CreateLoadTestConfigurationRequest = {
        name: formData.name!,
        url: formData.url!,
        method: formData.method,
        concurrent_users: formData.concurrent_users || 10,
        duration_seconds: formData.duration_seconds || 60,
        requests_per_second: formData.requests_per_second,
        headers: formData.headers,
        query_params: formData.query_params,
        body_template: formData.body_template,
        content_type: formData.content_type,
      };

      const result = await createConfig.mutateAsync(submitData);
      navigate(`/load-tests/${result.id}`);
    } catch (error) {
      // Error handled by hook
    }
  };

  return (
    <div className="min-h-screen bg-background p-6 pl-24">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <FadeIn>
          <div className="mb-6">
            <div className="flex items-center gap-2">
              <Gauge className="h-6 w-6 text-primary" />
              <h1 className="text-3xl font-bold">Create Benchmark</h1>
            </div>
            <p className="text-muted-foreground text-sm mt-2">
              Configure and start a new benchmark to test your API endpoints
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Form */}
          <div className="lg:col-span-2 space-y-5">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Basic Configuration Section */}
              <FadeIn delay={0.1}>
                <Card className="border rounded-lg">
                  <button
                    type="button"
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-accent/50 transition-colors rounded-t-lg"
                    onClick={() => {}}
                  >
                    <div className="flex items-center gap-2 text-lg font-semibold">
                      <Zap className="h-4 w-4 text-primary" />
                      Basic Configuration
                    </div>
                    <ChevronDown className="h-4 w-4 shrink-0 transition-transform duration-200" />
                  </button>
                  <CardContent className="px-6 pb-6">
                    <div className="space-y-4 pt-2">
                      {/* Test Name */}
                      <div className="space-y-1.5">
                        <Label htmlFor="name" className="text-xs font-medium">
                          Name <span className="text-destructive">*</span>
                        </Label>
                        <Input
                          id="name"
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          placeholder="e.g., API Benchmark"
                          className="h-9"
                          required
                        />
                      </div>

                      {/* Endpoint URL */}
                      <div className="space-y-1.5">
                        <Label htmlFor="url" className="text-xs font-medium">
                          Endpoint URL <span className="text-destructive">*</span>
                        </Label>
                        <Input
                          id="url"
                          type="url"
                          value={formData.url}
                          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                          placeholder="https://api.example.com/api/users"
                          className="h-9 font-mono text-sm"
                          required
                        />
                      </div>

                      {/* HTTP Method */}
                      <div className="space-y-1.5">
                        <Label className="text-xs font-medium">
                          HTTP Method <span className="text-destructive">*</span>
                        </Label>
                        <ToggleGroup
                          type="single"
                          value={formData.method || 'GET'}
                          onValueChange={(value) => {
                            if (value) setFormData({ ...formData, method: value });
                          }}
                          className="justify-start gap-2"
                        >
                          {HTTP_METHODS.map((method) => (
                            <ToggleGroupItem
                              key={method}
                              value={method}
                              className="px-4 h-9 font-mono text-sm border border-input data-[state=on]:bg-foreground data-[state=on]:text-background data-[state=on]:border-foreground"
                            >
                              {method}
                            </ToggleGroupItem>
                          ))}
                        </ToggleGroup>
                      </div>

                      {/* Content Type */}
                      <div className="space-y-1.5">
                        <Label htmlFor="contentType" className="text-xs font-medium">
                          Content Type <span className="text-destructive">*</span>
                        </Label>
                        <Select
                          value={formData.content_type || 'application/json'}
                          onValueChange={(value) =>
                            setFormData({ ...formData, content_type: value })
                          }
                        >
                          <SelectTrigger id="contentType" className="h-9">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="application/json" className="text-sm">
                              application/json
                            </SelectItem>
                            <SelectItem
                              value="application/x-www-form-urlencoded"
                              className="text-sm"
                            >
                              application/x-www-form-urlencoded
                            </SelectItem>
                            <SelectItem value="text/plain" className="text-sm">
                              text/plain
                            </SelectItem>
                            <SelectItem value="application/xml" className="text-sm">
                              application/xml
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Load Test Parameters */}
                      <div className="grid grid-cols-3 gap-3">
                        <div className="space-y-1.5">
                          <Label htmlFor="concurrent_users" className="text-xs font-medium">
                            Concurrent Threads
                          </Label>
                          <Input
                            id="concurrent_users"
                            type="number"
                            min="1"
                            max="1000"
                            value={formData.concurrent_users}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                concurrent_users: parseInt(e.target.value) || 10,
                              })
                            }
                            className="h-9"
                            required
                          />
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="duration_seconds" className="text-xs font-medium">
                            Duration (s)
                          </Label>
                          <Input
                            id="duration_seconds"
                            type="number"
                            min="1"
                            max="3600"
                            value={formData.duration_seconds}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                duration_seconds: parseInt(e.target.value) || 60,
                              })
                            }
                            className="h-9"
                            required
                          />
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="requests_per_second" className="text-xs font-medium">
                            Rate Limit (req/s)
                          </Label>
                          <Input
                            id="requests_per_second"
                            type="number"
                            min="1"
                            value={formData.requests_per_second || ''}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                requests_per_second: e.target.value
                                  ? parseInt(e.target.value)
                                  : undefined,
                              })
                            }
                            placeholder="Optional"
                            className="h-9"
                          />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </FadeIn>

              {/* Advanced Configuration Section */}
              <FadeIn delay={0.2}>
                <Card className="border rounded-lg">
                  <button
                    type="button"
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-accent/50 transition-colors rounded-t-lg"
                    onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
                  >
                    <div className="flex items-center gap-2 text-lg font-semibold">
                      <Settings2 className="h-4 w-4 text-primary" />
                      Advanced
                    </div>
                    <ChevronDown
                      className={`h-4 w-4 shrink-0 transition-transform duration-200 ${
                        isAdvancedOpen ? 'rotate-180' : ''
                      }`}
                    />
                  </button>
                  {isAdvancedOpen && (
                    <CardContent className="px-6 pb-6">
                      <div className="space-y-4 pt-2">
                        {/* Headers */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Label className="text-xs font-medium">Headers</Label>
                              <Badge
                                variant="outline"
                                className="text-[10px] h-4 px-1.5 font-normal"
                              >
                                Optional
                              </Badge>
                            </div>
                            <Button
                              type="button"
                              onClick={() => {
                                const newEntries = [...headerEntries, { key: '', value: '' }];
                                setHeaderEntries(newEntries);
                              }}
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                            >
                              <Plus className="h-3 w-3 mr-1" />
                              Add
                            </Button>
                          </div>
                          {headerEntries.length === 0 ? (
                            <div className="border border-dashed rounded-md p-3 bg-muted/10">
                              <p className="text-xs text-muted-foreground text-center">
                                No headers added yet. Click "Add" to include custom headers.
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-1.5 border rounded-md p-3 bg-muted/20">
                              {headerEntries.map((entry, index) => (
                                <div key={index} className="flex gap-1.5">
                                  <Button
                                    type="button"
                                    onClick={() => {
                                      const newEntries = headerEntries.filter(
                                        (_, i) => i !== index
                                      );
                                      setHeaderEntries(newEntries);
                                      updateHeaders(newEntries);
                                    }}
                                    size="icon"
                                    variant="ghost"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                  >
                                    <CircleMinus className="h-4 w-4" />
                                  </Button>
                                  <Input
                                    placeholder="Key (e.g., Authorization)"
                                    value={entry.key}
                                    onChange={(e) => {
                                      const newEntries = [...headerEntries];
                                      newEntries[index].key = e.target.value;
                                      setHeaderEntries(newEntries);
                                      updateHeaders(newEntries);
                                    }}
                                    className="flex-1 h-8 text-sm"
                                  />
                                  <Input
                                    placeholder="Value (e.g., Bearer token123)"
                                    value={entry.value}
                                    onChange={(e) => {
                                      const newEntries = [...headerEntries];
                                      newEntries[index].value = e.target.value;
                                      setHeaderEntries(newEntries);
                                      updateHeaders(newEntries);
                                    }}
                                    className="flex-1 h-8 text-sm"
                                  />
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Query Parameters */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Label className="text-xs font-medium">Query Parameters</Label>
                              <Badge
                                variant="outline"
                                className="text-[10px] h-4 px-1.5 font-normal"
                              >
                                Optional
                              </Badge>
                            </div>
                            <Button
                              type="button"
                              onClick={() => {
                                const newEntries = [...queryParamEntries, { key: '', value: '' }];
                                setQueryParamEntries(newEntries);
                              }}
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                            >
                              <Plus className="h-3 w-3 mr-1" />
                              Add
                            </Button>
                          </div>
                          {queryParamEntries.length === 0 ? (
                            <div className="border border-dashed rounded-md p-3 bg-muted/10">
                              <p className="text-xs text-muted-foreground text-center">
                                No query parameters added yet. Click "Add" to include URL
                                parameters.
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-1.5 border rounded-md p-3 bg-muted/20">
                              {queryParamEntries.map((entry, index) => (
                                <div key={index} className="flex gap-1.5">
                                  <Button
                                    type="button"
                                    onClick={() => {
                                      const newEntries = queryParamEntries.filter(
                                        (_, i) => i !== index
                                      );
                                      setQueryParamEntries(newEntries);
                                      updateQueryParams(newEntries);
                                    }}
                                    size="icon"
                                    variant="ghost"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                  >
                                    <CircleMinus className="h-4 w-4" />
                                  </Button>
                                  <Input
                                    placeholder="Key (e.g., api_key)"
                                    value={entry.key}
                                    onChange={(e) => {
                                      const newEntries = [...queryParamEntries];
                                      newEntries[index].key = e.target.value;
                                      setQueryParamEntries(newEntries);
                                      updateQueryParams(newEntries);
                                    }}
                                    className="flex-1 h-8 text-sm"
                                  />
                                  <Input
                                    placeholder="Value (e.g., 12345)"
                                    value={entry.value}
                                    onChange={(e) => {
                                      const newEntries = [...queryParamEntries];
                                      newEntries[index].value = e.target.value;
                                      setQueryParamEntries(newEntries);
                                      updateQueryParams(newEntries);
                                    }}
                                    className="flex-1 h-8 text-sm"
                                  />
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Body Template */}
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <Label htmlFor="body_template" className="text-xs font-medium">
                              Request Body Template
                            </Label>
                            <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-normal">
                              Optional
                            </Badge>
                          </div>
                          <Textarea
                            id="body_template"
                            value={formData.body_template || ''}
                            onChange={(e) =>
                              setFormData({ ...formData, body_template: e.target.value })
                            }
                            placeholder='{"event": "load_test", "timestamp": "{{timestamp}}"}'
                            className="font-mono min-h-[100px] text-sm"
                          />
                          <p className="text-xs text-muted-foreground">
                            Use template variables like {`{{timestamp}}`} or {`{{data}}`} for
                            dynamic content
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  )}
                </Card>
              </FadeIn>

              {/* Submit Button */}
              <FadeIn delay={0.3}>
                <div className="flex gap-3 justify-end pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate('/load-tests')}
                    disabled={createConfig.isPending}
                    className="h-9"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createConfig.isPending} className="h-9">
                    {createConfig.isPending ? (
                      <>
                        <div className="h-3.5 w-3.5 border-2 border-background border-t-transparent rounded-full animate-spin mr-2" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Gauge className="h-3.5 w-3.5 mr-2" />
                        Create & Start Test
                      </>
                    )}
                  </Button>
                </div>
              </FadeIn>
            </form>
          </div>

          {/* Right Column - Information Box (Sticky) */}
          <div className="lg:col-span-1">
            <FadeIn delay={0.4}>
              <Card className="border sticky top-6">
                <CardContent className="p-6">
                  <h4 className="text-sm font-semibold mb-3">About Benchmarking</h4>
                  <div className="space-y-3 text-sm text-muted-foreground">
                    <p>
                      Benchmarking helps you understand how your API performs under various load
                      conditions and identify potential bottlenecks or performance issues.
                    </p>
                    <div className="space-y-2 mt-4">
                      <p>
                        <strong className="text-foreground">Concurrent Threads:</strong>
                      </p>
                      <p className="text-xs">
                        The number of simultaneous threads making requests to your API. Higher
                        values simulate more traffic but require more resources.
                      </p>
                    </div>
                    <div className="space-y-2 mt-4">
                      <p>
                        <strong className="text-foreground">Duration:</strong>
                      </p>
                      <p className="text-xs">
                        How long the benchmark will run. Benchmarks can run from 1 second up to 1
                        hour (3600 seconds).
                      </p>
                    </div>
                    <div className="space-y-2 mt-4">
                      <p>
                        <strong className="text-foreground">Rate Limiting:</strong>
                      </p>
                      <p className="text-xs">
                        Optional limit on requests per second. Leave empty for unlimited rate.
                        Useful for testing specific traffic patterns.
                      </p>
                    </div>
                    <div className="space-y-2 mt-4">
                      <p>
                        <strong className="text-foreground">What Gets Tested:</strong>
                      </p>
                      <ul className="list-disc list-inside space-y-1 ml-2 text-xs">
                        <li>Response times (avg, min, max, p95, p99)</li>
                        <li>Success vs failure rates</li>
                        <li>Total requests processed</li>
                        <li>API stability under load</li>
                      </ul>
                    </div>
                    <div className="space-y-2 mt-4">
                      <p>
                        <strong className="text-foreground">Best Practices:</strong>
                      </p>
                      <ul className="list-disc list-inside space-y-1 ml-2 text-xs">
                        <li>Start with lower concurrent threads</li>
                        <li>Gradually increase load to find limits</li>
                        <li>Monitor server resources during tests</li>
                        <li>Test in staging before production</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </FadeIn>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewLoadTestPage;
