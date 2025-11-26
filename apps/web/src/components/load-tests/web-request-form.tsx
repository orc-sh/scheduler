import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useCreateWebhook, useUpdateWebhook } from '@/hooks/use-load-tests';
import type { CreateWebhookRequest, UpdateWebhookRequest, Webhook } from '@/types/load-test.types';

interface WebRequestFormProps {
  collectionId: string;
  webhook?: Webhook;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];

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
  const [headers, setHeaders] = useState(
    webhook?.headers ? JSON.stringify(webhook.headers, null, 2) : ''
  );
  const [queryParams, setQueryParams] = useState(
    webhook?.query_params ? JSON.stringify(webhook.query_params, null, 2) : ''
  );
  const [bodyTemplate, setBodyTemplate] = useState(webhook?.body_template || '');
  const [contentType, setContentType] = useState(webhook?.content_type || 'application/json');
  const [order, setOrder] = useState(webhook?.order?.toString() || '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let parsedHeaders: Record<string, string> | undefined;
    let parsedQueryParams: Record<string, string> | undefined;

    try {
      if (headers.trim()) {
        parsedHeaders = JSON.parse(headers);
      }
    } catch (error) {
      alert('Invalid JSON in headers field');
      return;
    }

    try {
      if (queryParams.trim()) {
        parsedQueryParams = JSON.parse(queryParams);
      }
    } catch (error) {
      alert('Invalid JSON in query parameters field');
      return;
    }

    const data: CreateWebhookRequest | UpdateWebhookRequest = {
      url,
      method,
      headers: parsedHeaders,
      query_params: parsedQueryParams,
      body_template: bodyTemplate || undefined,
      content_type: contentType,
      order: order ? parseInt(order, 10) : undefined,
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
    setHeaders('');
    setQueryParams('');
    setBodyTemplate('');
    setContentType('application/json');
    setOrder('');
  };

  const isLoading = createWebhook.isPending || updateWebhook.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{webhook ? 'Edit Web Request' : 'Add Web Request'}</DialogTitle>
          <DialogDescription>
            Configure the HTTP request to be executed during the load test.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
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
              <Label htmlFor="order">Execution Order</Label>
              <Input
                id="order"
                type="number"
                value={order}
                onChange={(e) => setOrder(e.target.value)}
                placeholder="0"
                min="0"
              />
              <p className="text-xs text-muted-foreground">
                Lower numbers execute first. Leave empty for auto-assignment.
              </p>
            </div>
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

          <div className="space-y-2">
            <Label htmlFor="headers">Headers (JSON)</Label>
            <Textarea
              id="headers"
              value={headers}
              onChange={(e) => setHeaders(e.target.value)}
              placeholder='{"Authorization": "Bearer token", "Content-Type": "application/json"}'
              rows={4}
              className="font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="queryParams">Query Parameters (JSON)</Label>
            <Textarea
              id="queryParams"
              value={queryParams}
              onChange={(e) => setQueryParams(e.target.value)}
              placeholder='{"page": "1", "limit": "10"}'
              rows={3}
              className="font-mono text-sm"
            />
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

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : webhook ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
