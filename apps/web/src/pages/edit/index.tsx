import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import {
  Plus,
  CircleMinus,
  Globe,
  AlertCircle,
  Zap,
  Info,
  Settings2,
  ArrowLeft,
  Pencil,
} from 'lucide-react';
import { useWebhook, useUpdateWebhook } from '@/hooks/use-webhooks';
import type { HttpMethod } from '@/types/webhook.types';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Switch } from '@/components/ui/switch';

// Validation schema
const webhookSchema = z.object({
  jobName: z.string().min(1, 'Job name is required').max(255, 'Job name is too long'),
  schedule: z
    .string()
    .min(1, 'Schedule is required')
    .regex(/^[\d\s\*\,\-\/]+$/, 'Invalid cron expression'),
  timezone: z.string().min(1, 'Timezone is required'),
  enabled: z.boolean(),
  webhookUrl: z.string().url('Must be a valid URL'),
  httpMethod: z.enum(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']),
  contentType: z.string().min(1, 'Content type is required'),
  bodyTemplate: z.string().optional(),
  headers: z.array(z.object({ key: z.string(), value: z.string() })),
  queryParams: z.array(z.object({ key: z.string(), value: z.string() })),
});

type WebhookFormData = z.infer<typeof webhookSchema>;

// Common cron presets
const CRON_PRESETS = [
  { label: 'Every 5 seconds', value: '*/5 * * * * *', description: 'Runs every 5 seconds' },
  { label: 'Every 10 seconds', value: '*/10 * * * * *', description: 'Runs every 10 seconds' },
  { label: 'Every minute', value: '* * * * *', description: 'Runs every minute' },
  { label: 'Every 5 minutes', value: '*/5 * * * *', description: 'Runs every 5 minutes' },
  { label: 'Every hour', value: '0 * * * *', description: 'Runs at minute 0 of every hour' },
  { label: 'Every day at 9 AM', value: '0 9 * * *', description: 'Runs daily at 9:00 AM' },
  {
    label: 'Every Monday at 9 AM',
    value: '0 9 * * 1',
    description: 'Runs every Monday at 9:00 AM',
  },
  { label: 'First day of month', value: '0 0 1 * *', description: 'Runs at midnight on the 1st' },
];

// Common timezones
const TIMEZONES = [
  { label: 'GMT', value: 'GMT' },
  { label: 'America/New_York (EST)', value: 'America/New_York' },
  { label: 'America/Chicago (CST)', value: 'America/Chicago' },
  { label: 'America/Los_Angeles (PST)', value: 'America/Los_Angeles' },
  { label: 'Europe/London', value: 'Europe/London' },
  { label: 'Europe/Paris', value: 'Europe/Paris' },
  { label: 'Asia/Tokyo', value: 'Asia/Tokyo' },
  { label: 'Asia/Shanghai', value: 'Asia/Shanghai' },
  { label: 'Australia/Sydney', value: 'Australia/Sydney' },
];

// HTTP methods with subtle styling
const HTTP_METHODS: { value: HttpMethod; label: string }[] = [
  { value: 'GET', label: 'GET' },
  { value: 'POST', label: 'POST' },
  { value: 'PUT', label: 'PUT' },
  { value: 'PATCH', label: 'PATCH' },
  { value: 'DELETE', label: 'DELETE' },
];

const EditWebhookPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const updateWebhook = useUpdateWebhook();
  const { data: webhook, isLoading, isError } = useWebhook(id!);
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<WebhookFormData>({
    resolver: zodResolver(webhookSchema),
    defaultValues: {
      timezone: 'GMT',
      enabled: true,
      httpMethod: 'POST',
      contentType: 'application/json',
      headers: [],
      queryParams: [],
    },
  });

  const headers = watch('headers');
  const queryParams = watch('queryParams');
  const httpMethod = watch('httpMethod');
  const enabled = watch('enabled');

  // Check for returned cron expression from cron builder
  useEffect(() => {
    const selectedCron = sessionStorage.getItem('selectedCronExpression');
    if (selectedCron) {
      setValue('schedule', selectedCron);
      sessionStorage.removeItem('selectedCronExpression');
    }
  }, [setValue]);

  // Populate form when webhook data loads
  useEffect(() => {
    if (webhook) {
      reset({
        jobName: webhook.job?.name || '',
        schedule: webhook.job?.schedule || '',
        timezone: webhook.job?.timezone || 'GMT',
        enabled: webhook.job?.enabled ?? true,
        webhookUrl: webhook.url,
        httpMethod: webhook.method,
        contentType: webhook.content_type,
        bodyTemplate: webhook.body_template || '',
        headers: webhook.headers
          ? Object.entries(webhook.headers).map(([key, value]) => ({ key, value }))
          : [],
        queryParams: webhook.query_params
          ? Object.entries(webhook.query_params).map(([key, value]) => ({ key, value }))
          : [],
      });
      if (webhook.job?.schedule) {
        setSelectedPreset(webhook.job.schedule);
      }
    }
  }, [webhook, reset, setSelectedPreset]);

  const addHeader = () => {
    setValue('headers', [...headers, { key: '', value: '' }]);
  };

  const removeHeader = (index: number) => {
    setValue(
      'headers',
      headers.filter((_, i) => i !== index)
    );
  };

  const addQueryParam = () => {
    setValue('queryParams', [...queryParams, { key: '', value: '' }]);
  };

  const removeQueryParam = (index: number) => {
    setValue(
      'queryParams',
      queryParams.filter((_, i) => i !== index)
    );
  };

  const applyPreset = (preset: string) => {
    setValue('schedule', preset);
    setSelectedPreset(preset);
  };

  const onSubmit = async (data: WebhookFormData) => {
    if (!id) return;

    try {
      // Convert headers and query params to objects
      const headersObj = data.headers.reduce(
        (acc, { key, value }) => {
          if (key.trim()) acc[key] = value;
          return acc;
        },
        {} as Record<string, string>
      );

      const queryParamsObj = data.queryParams.reduce(
        (acc, { key, value }) => {
          if (key.trim()) acc[key] = value;
          return acc;
        },
        {} as Record<string, string>
      );

      await updateWebhook.mutateAsync({
        id,
        data: {
          url: data.webhookUrl,
          method: data.httpMethod,
          headers: Object.keys(headersObj).length > 0 ? headersObj : undefined,
          query_params: Object.keys(queryParamsObj).length > 0 ? queryParamsObj : undefined,
          body_template: data.bodyTemplate || undefined,
          content_type: data.contentType,
          job: {
            name: data.jobName,
            schedule: data.schedule,
            timezone: data.timezone,
            enabled: data.enabled,
          },
        },
      });

      // Redirect to dashboard after success
      setTimeout(() => navigate('/'), 1500);
    } catch (error) {
      console.error('Failed to update webhook:', error);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-6 pl-24">
        <div className="container mx-auto space-y-6 max-w-4xl">
          <FadeIn>
            <div className="flex items-center gap-2.5">
              <Skeleton className="h-7 w-7 rounded" />
              <div className="flex-1">
                <Skeleton className="h-8 w-48 mb-2" />
                <Skeleton className="h-4 w-96" />
              </div>
            </div>
          </FadeIn>

          <div className="space-y-4">
            <Skeleton className="h-64 w-full rounded-lg" />
            <Skeleton className="h-64 w-full rounded-lg" />
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
                The webhook you're trying to edit could not be found.
              </p>
              <Button onClick={() => navigate('/')}>Return to Dashboard</Button>
            </div>
          </FadeIn>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background p-6 pl-24">
        <div className="container mx-auto max-w-7xl">
          {/* Header */}
          <FadeIn>
            <div className="mb-6">
              <div className="flex items-center gap-2">
                <Zap className="h-6 w-6 text-primary" />
                <h1 className="text-3xl font-bold">{webhook.job?.name || 'Unnamed Webhook'}</h1>
              </div>
              <p className="text-muted-foreground text-sm mt-2">{webhook.url}</p>
            </div>
          </FadeIn>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Form */}
            <div className="lg:col-span-2 space-y-6">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                {/* Basic Configuration Section */}
                <FadeIn delay={0.1}>
                  <Card className="border rounded-lg">
                    <div className="w-full px-6 py-4 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-lg font-semibold">
                        <Zap className="h-4 w-4 text-primary" />
                        Basic Configuration
                      </div>
                    </div>
                    <CardContent className="px-6 pb-6">
                      <div className="space-y-4 pt-2">
                        {/* Job Name */}
                        <div className="space-y-1.5">
                          <Label htmlFor="jobName" className="text-xs font-medium">
                            Name <span className="text-destructive">*</span>
                          </Label>
                          <Input
                            id="jobName"
                            {...register('jobName')}
                            placeholder="e.g., Daily Report Generator"
                            className="h-9"
                          />
                          {errors.jobName && (
                            <p className="text-xs text-destructive flex items-center gap-1">
                              <AlertCircle className="h-3 w-3" />
                              {errors.jobName.message}
                            </p>
                          )}
                        </div>

                        {/* Webhook URL */}
                        <div className="space-y-1.5">
                          <Label htmlFor="webhookUrl" className="text-xs font-medium">
                            Webhook URL <span className="text-destructive">*</span>
                          </Label>
                          <Input
                            id="webhookUrl"
                            {...register('webhookUrl')}
                            placeholder="https://api.example.com/webhook"
                            type="url"
                            className="h-9 font-mono text-sm"
                          />
                          {errors.webhookUrl && (
                            <p className="text-xs text-destructive flex items-center gap-1">
                              <AlertCircle className="h-3 w-3" />
                              {errors.webhookUrl.message}
                            </p>
                          )}
                        </div>

                        {/* Schedule & Timezone */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="schedule" className="text-xs font-medium">
                              Schedule (Cron Expression) <span className="text-destructive">*</span>
                            </Label>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 px-2 text-xs text-muted-foreground hover:text-primary"
                                  onClick={() => {
                                    const currentSchedule = watch('schedule');
                                    const returnUrl = `/edit/${id}`;
                                    navigate(
                                      `/cron-builder?value=${encodeURIComponent(currentSchedule || '')}&return=${encodeURIComponent(returnUrl)}`
                                    );
                                  }}
                                >
                                  <Info className="h-3 w-3 mr-1" />
                                  Build Expression
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="left">
                                <p className="text-xs">Open cron expression builder</p>
                              </TooltipContent>
                            </Tooltip>
                          </div>

                          {/* Schedule Input and Timezone in a row */}
                          <div className="grid grid-cols-1 md:grid-cols-[1fr,200px] gap-2">
                            <div className="space-y-1.5">
                              <Input
                                id="schedule"
                                {...register('schedule')}
                                placeholder="0 9 * * *"
                                className="font-mono h-9 text-sm"
                              />
                              {errors.schedule && (
                                <p className="text-xs text-destructive flex items-center gap-1">
                                  <AlertCircle className="h-3 w-3" />
                                  {errors.schedule.message}
                                </p>
                              )}
                            </div>

                            <div className="space-y-1.5">
                              <Select
                                value={watch('timezone')}
                                onValueChange={(value) => setValue('timezone', value)}
                              >
                                <SelectTrigger id="timezone" className="h-9 text-left">
                                  <Globe className="h-3.5 w-3.5 mr-1.5" />
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {TIMEZONES.map((tz) => (
                                    <SelectItem key={tz.value} value={tz.value} className="text-sm">
                                      {tz.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          </div>

                          {/* Cron Presets */}
                          <div className="space-y-1.5">
                            <p className="text-xs text-muted-foreground">Quick presets:</p>
                            <div className="flex flex-wrap gap-1.5">
                              {CRON_PRESETS.map((preset) => (
                                <Tooltip key={preset.value}>
                                  <TooltipTrigger asChild>
                                    <Button
                                      type="button"
                                      variant={
                                        selectedPreset === preset.value ? 'default' : 'outline'
                                      }
                                      size="sm"
                                      onClick={() => applyPreset(preset.value)}
                                      className="h-7 text-xs px-2.5"
                                    >
                                      {preset.label}
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="text-xs">{preset.description}</p>
                                  </TooltipContent>
                                </Tooltip>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Enabled Toggle */}
                        <div className="flex items-center justify-between space-y-0 rounded-md border p-4">
                          <div className="space-y-0.5">
                            <Label htmlFor="enabled" className="text-xs font-medium">
                              Enabled
                            </Label>
                            <p className="text-xs text-muted-foreground">
                              Enable or disable this scheduled webhook
                            </p>
                          </div>
                          <Switch
                            id="enabled"
                            checked={enabled}
                            onCheckedChange={(checked) => setValue('enabled', checked)}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </FadeIn>

                {/* Advanced Configuration Section */}
                <FadeIn delay={0.2}>
                  <Card className="border rounded-lg">
                    <div className="w-full px-6 py-4 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-lg font-semibold">
                        <Settings2 className="h-4 w-4 text-primary" />
                        Advanced
                      </div>
                    </div>
                    <CardContent className="px-6 pb-6">
                      <div className="space-y-4 pt-2">
                        {/* HTTP Method & Content Type */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* HTTP Method */}
                          <div className="space-y-1.5">
                            <Label className="text-xs font-medium">
                              HTTP Method <span className="text-destructive">*</span>
                            </Label>
                            <ToggleGroup
                              type="single"
                              value={httpMethod}
                              onValueChange={(value) => {
                                if (value) setValue('httpMethod', value as HttpMethod);
                              }}
                              className="justify-start gap-2"
                            >
                              {HTTP_METHODS.map((method) => (
                                <ToggleGroupItem
                                  key={method.value}
                                  value={method.value}
                                  className="px-4 h-9 font-mono text-sm border border-input data-[state=on]:bg-foreground data-[state=on]:text-background data-[state=on]:border-foreground"
                                >
                                  {method.label}
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
                              value={watch('contentType')}
                              onValueChange={(value) => setValue('contentType', value)}
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
                        </div>

                        {/* Headers */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label className="text-xs font-medium">
                              Headers
                              <span className="text-xs text-muted-foreground font-normal ml-1.5">
                                (Optional)
                              </span>
                            </Label>
                            <Button
                              type="button"
                              onClick={addHeader}
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                            >
                              <Plus className="h-3 w-3 mr-1" />
                              Add
                            </Button>
                          </div>
                          {headers.length === 0 ? (
                            <div className="border border-dashed rounded-md p-3 bg-muted/10">
                              <p className="text-xs text-muted-foreground text-center">
                                No headers added yet. Click "Add" to include custom headers.
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-1.5 border rounded-md p-3 bg-muted/20">
                              {headers.map((_, index) => (
                                <div key={index} className="flex gap-1.5">
                                  <Button
                                    type="button"
                                    onClick={() => removeHeader(index)}
                                    size="icon"
                                    variant="ghost"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                  >
                                    <CircleMinus className="h-4 w-4" />
                                  </Button>
                                  <Input
                                    {...register(`headers.${index}.key`)}
                                    placeholder="Key (e.g., Authorization)"
                                    className="flex-1 h-8 text-sm"
                                  />
                                  <Input
                                    {...register(`headers.${index}.value`)}
                                    placeholder="Value (e.g., Bearer token123)"
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
                            <Label className="text-xs font-medium">
                              Query Parameters
                              <span className="text-xs text-muted-foreground font-normal ml-1.5">
                                (Optional)
                              </span>
                            </Label>
                            <Button
                              type="button"
                              onClick={addQueryParam}
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                            >
                              <Plus className="h-3 w-3 mr-1" />
                              Add
                            </Button>
                          </div>
                          {queryParams.length === 0 ? (
                            <div className="border border-dashed rounded-md p-3 bg-muted/10">
                              <p className="text-xs text-muted-foreground text-center">
                                No query parameters added yet. Click "Add" to include URL
                                parameters.
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-1.5 border rounded-md p-3 bg-muted/20">
                              {queryParams.map((_, index) => (
                                <div key={index} className="flex gap-1.5">
                                  <Button
                                    type="button"
                                    onClick={() => removeQueryParam(index)}
                                    size="icon"
                                    variant="ghost"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                  >
                                    <CircleMinus className="h-4 w-4" />
                                  </Button>
                                  <Input
                                    {...register(`queryParams.${index}.key`)}
                                    placeholder="Key (e.g., api_key)"
                                    className="flex-1 h-8 text-sm"
                                  />
                                  <Input
                                    {...register(`queryParams.${index}.value`)}
                                    placeholder="Value (e.g., 12345)"
                                    className="flex-1 h-8 text-sm"
                                  />
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Body Template */}
                        <div className="space-y-1.5">
                          <Label htmlFor="bodyTemplate" className="text-xs font-medium">
                            Request Body Template
                            <span className="text-xs text-muted-foreground font-normal ml-1.5">
                              (Optional)
                            </span>
                          </Label>
                          <Textarea
                            id="bodyTemplate"
                            {...register('bodyTemplate')}
                            placeholder='{"event": "scheduled", "timestamp": "{{timestamp}}"}'
                            className="font-mono min-h-[100px] text-sm"
                          />
                          <p className="text-xs text-muted-foreground">
                            Use template variables like {`{{timestamp}}`} or {`{{data}}`} for
                            dynamic content
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </FadeIn>

                {/* Submit Button */}
                <FadeIn delay={0.3}>
                  <div className="flex gap-3 justify-end pt-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => navigate('/')}
                      disabled={isSubmitting}
                      className="h-9"
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={isSubmitting} className="h-9">
                      {isSubmitting ? (
                        <>
                          <div className="h-3.5 w-3.5 border-2 border-background border-t-transparent rounded-full animate-spin mr-2" />
                          Updating...
                        </>
                      ) : (
                        <>Update</>
                      )}
                    </Button>
                  </div>
                </FadeIn>
              </form>
            </div>

            {/* Right Column - Documentation (Sticky) */}
            <div className="lg:col-span-1">
              <FadeIn delay={0.4}>
                <Card className="border sticky top-6">
                  <CardContent className="p-6">
                    <h4 className="text-sm font-semibold mb-3">Cron Expression Format</h4>
                    <div className="space-y-3 text-sm text-muted-foreground">
                      <p>
                        A cron expression consists of 6 fields separated by spaces:
                        <code className="ml-2 px-2 py-1 bg-muted rounded font-mono text-foreground block mt-1">
                          second minute hour day month weekday
                        </code>
                      </p>
                      <div className="space-y-2 mt-4">
                        <p>
                          <strong className="text-foreground">Special characters:</strong>
                        </p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>
                            <code className="px-1.5 py-0.5 bg-muted rounded font-mono text-foreground">
                              *
                            </code>{' '}
                            - Any value
                          </li>
                          <li>
                            <code className="px-1.5 py-0.5 bg-muted rounded font-mono text-foreground">
                              ,
                            </code>{' '}
                            - Value list separator (e.g., 1,3,5)
                          </li>
                          <li>
                            <code className="px-1.5 py-0.5 bg-muted rounded font-mono text-foreground">
                              -
                            </code>{' '}
                            - Range of values (e.g., 1-5)
                          </li>
                          <li>
                            <code className="px-1.5 py-0.5 bg-muted rounded font-mono text-foreground">
                              /
                            </code>{' '}
                            - Step values (e.g., */5 means every 5)
                          </li>
                        </ul>
                      </div>
                      <div className="space-y-2 mt-4">
                        <p>
                          <strong className="text-foreground">Field ranges:</strong>
                        </p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>Second: 0-59</li>
                          <li>Minute: 0-59</li>
                          <li>Hour: 0-23</li>
                          <li>Day of month: 1-31</li>
                          <li>Month: 1-12</li>
                          <li>Day of week: 0-7 (0 and 7 are Sunday)</li>
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
    </TooltipProvider>
  );
};

export default EditWebhookPage;
