import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Plus, CircleMinus } from 'lucide-react';
import { useCreateWebhook, useUpdateWebhook } from '@/hooks/use-collections';
import type { CreateWebhookRequest, UpdateWebhookRequest, Webhook } from '@/types/collection.types';

interface WebRequestFormProps {
  collectionId: string;
  webhook?: Webhook;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];

type KeyValuePair = { key: string; value: string };

export const WebRequestForm = ({
  collectionId,
  webhook,
  open,
  onOpenChange,
}: WebRequestFormProps) => {
  const createWebhook = useCreateWebhook();
  const updateWebhook = useUpdateWebhook();

  const [url, setUrl] = useState(webhook?.url || '');
  const [method, setMethod] = useState(webhook?.method || 'GET');
  const [headers, setHeaders] = useState<KeyValuePair[]>([]);
  const [queryParams, setQueryParams] = useState<KeyValuePair[]>([]);
  const [bodyTemplate, setBodyTemplate] = useState(webhook?.body_template || '');
  const [contentType, setContentType] = useState(webhook?.content_type || 'application/json');

  // Initialize form when webhook changes or dialog opens
  useEffect(() => {
    if (open) {
      setUrl(webhook?.url || '');
      setMethod(webhook?.method || 'GET');
      setBodyTemplate(webhook?.body_template || '');
      setContentType(webhook?.content_type || 'application/json');

      // Convert headers object to key-value pairs
      if (webhook?.headers) {
        const headerPairs: KeyValuePair[] = Object.entries(webhook.headers).map(([key, value]) => ({
          key,
          value: String(value),
        }));
        setHeaders(headerPairs.length > 0 ? headerPairs : []);
      } else {
        setHeaders([]);
      }

      // Convert query_params object to key-value pairs
      if (webhook?.query_params) {
        const queryPairs: KeyValuePair[] = Object.entries(webhook.query_params).map(
          ([key, value]) => ({
            key,
            value: String(value),
          })
        );
        setQueryParams(queryPairs.length > 0 ? queryPairs : []);
      } else {
        setQueryParams([]);
      }
    }
  }, [webhook, open]);

  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '' }]);
  };

  const removeHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index));
  };

  const updateHeader = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...headers];
    updated[index] = { ...updated[index], [field]: value };
    setHeaders(updated);
  };

  const addQueryParam = () => {
    setQueryParams([...queryParams, { key: '', value: '' }]);
  };

  const removeQueryParam = (index: number) => {
    setQueryParams(queryParams.filter((_, i) => i !== index));
  };

  const updateQueryParam = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...queryParams];
    updated[index] = { ...updated[index], [field]: value };
    setQueryParams(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Convert headers array to object
    const headersObj = headers.reduce(
      (acc, { key, value }) => {
        if (key.trim()) acc[key] = value;
        return acc;
      },
      {} as Record<string, string>
    );

    // Convert query params array to object
    const queryParamsObj = queryParams.reduce(
      (acc, { key, value }) => {
        if (key.trim()) acc[key] = value;
        return acc;
      },
      {} as Record<string, string>
    );

    const data: CreateWebhookRequest | UpdateWebhookRequest = {
      url,
      method,
      headers: Object.keys(headersObj).length > 0 ? headersObj : undefined,
      query_params: Object.keys(queryParamsObj).length > 0 ? queryParamsObj : undefined,
      body_template: bodyTemplate || undefined,
      content_type: contentType,
    };

    if (webhook) {
      await updateWebhook.mutateAsync({ webhookId: webhook.id, data });
    } else {
      await createWebhook.mutateAsync({ collectionId, data });
    }

    onOpenChange(false);
    // Reset form
    setUrl('');
    setMethod('GET');
    setHeaders([]);
    setQueryParams([]);
    setBodyTemplate('');
    setContentType('application/json');
  };

  const isLoading = createWebhook.isPending || updateWebhook.isPending;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{webhook ? 'Edit Web Request' : 'Add Web Request'}</SheetTitle>
          <SheetDescription>
            Configure the HTTP request to be executed during the load test.
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={handleSubmit} className="space-y-6 mt-6">
          <div className="space-y-2">
            <Label htmlFor="method">HTTP Method</Label>
            <Select value={method} onValueChange={setMethod}>
              <SelectTrigger id="method">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {HTTP_METHODS.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="url">URL *</Label>
            <Input
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://api.example.com/endpoint"
              required
            />
          </div>

          {/* Headers */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Label className="text-xs font-medium">Headers</Label>
                <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-normal">
                  Optional
                </Badge>
              </div>
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
                {headers.map((header, index) => (
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
                      value={header.key}
                      onChange={(e) => updateHeader(index, 'key', e.target.value)}
                      placeholder="Key (e.g., Authorization)"
                      className="flex-1 h-8 text-sm"
                    />
                    <Input
                      value={header.value}
                      onChange={(e) => updateHeader(index, 'value', e.target.value)}
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
              <div className="flex items-center gap-2">
                <Label className="text-xs font-medium">Query Parameters</Label>
                <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-normal">
                  Optional
                </Badge>
              </div>
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
                  No query parameters added yet. Click "Add" to include URL parameters.
                </p>
              </div>
            ) : (
              <div className="space-y-1.5 border rounded-md p-3 bg-muted/20">
                {queryParams.map((param, index) => (
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
                      value={param.key}
                      onChange={(e) => updateQueryParam(index, 'key', e.target.value)}
                      placeholder="Key (e.g., api_key)"
                      className="flex-1 h-8 text-sm"
                    />
                    <Input
                      value={param.value}
                      onChange={(e) => updateQueryParam(index, 'value', e.target.value)}
                      placeholder="Value (e.g., 12345)"
                      className="flex-1 h-8 text-sm"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {method !== 'GET' && method !== 'HEAD' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="contentType">Content Type</Label>
                <Input
                  id="contentType"
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value)}
                  placeholder="application/json"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bodyTemplate">Request Body</Label>
                <Textarea
                  id="bodyTemplate"
                  value={bodyTemplate}
                  onChange={(e) => setBodyTemplate(e.target.value)}
                  placeholder='{"key": "value"}'
                  rows={6}
                  className="font-mono text-sm"
                />
              </div>
            </>
          )}

          <SheetFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : webhook ? 'Update' : 'Create'}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
};
