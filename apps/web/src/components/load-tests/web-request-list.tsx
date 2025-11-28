import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Edit, Trash2, Plus } from 'lucide-react';
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
import { WebRequestForm } from './web-request-form';
import { useDeleteWebhook } from '@/hooks/use-collections';
import type { Webhook } from '@/types/collection.types';

interface WebRequestListProps {
  collectionId: string;
  webhooks: Webhook[];
}

export const WebRequestList = ({ collectionId, webhooks }: WebRequestListProps) => {
  const [editingWebhook, setEditingWebhook] = useState<Webhook | undefined>();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const deleteWebhook = useDeleteWebhook();

  const handleEdit = (webhook: Webhook) => {
    setEditingWebhook(webhook);
    setIsFormOpen(true);
  };

  const handleDelete = async (webhookId: string) => {
    await deleteWebhook.mutateAsync(webhookId);
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingWebhook(undefined);
  };

  const handleAddNew = () => {
    setEditingWebhook(undefined);
    setIsFormOpen(true);
  };

  if (webhooks.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/25 bg-muted/5 p-12 text-center">
        <div className="flex flex-col items-center justify-center gap-4">
          <div className="rounded-full bg-muted/50 p-4">
            <Plus className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-1">No Web Requests</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              Add web requests to your collection. Each request will be executed during the test.
            </p>
          </div>
          <Button onClick={handleAddNew} className="mt-4">
            <Plus className="mr-2 h-4 w-4" />
            Add Web Request
          </Button>
        </div>
        <WebRequestForm
          collectionId={collectionId}
          webhook={editingWebhook}
          open={isFormOpen}
          onOpenChange={handleFormClose}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Web Requests</h3>
          <p className="text-sm text-muted-foreground">
            {webhooks.length} request{webhooks.length !== 1 ? 's' : ''} configured
          </p>
        </div>
        <Button onClick={handleAddNew}>
          <Plus className="mr-2 h-4 w-4" />
          Add Web Request
        </Button>
      </div>

      <div className="space-y-3">
        {webhooks.map((webhook) => (
          <Card key={webhook.id} className="rounded-xl border-border/50">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <Badge variant="outline" className="font-mono">
                      {webhook.method}
                    </Badge>
                  </div>
                  <code className="text-sm font-mono break-all text-foreground">{webhook.url}</code>
                  {(webhook.headers || webhook.query_params || webhook.body_template) && (
                    <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                      {webhook.headers && Object.keys(webhook.headers).length > 0 && (
                        <div>Headers: {Object.keys(webhook.headers).length} header(s)</div>
                      )}
                      {webhook.query_params && Object.keys(webhook.query_params).length > 0 && (
                        <div>Query params: {Object.keys(webhook.query_params).length} param(s)</div>
                      )}
                      {webhook.body_template && <div>Has request body</div>}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(webhook)}
                    className="h-8 w-8"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This will permanently delete this web request from the collection. This
                          action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleDelete(webhook.id)}
                          className="bg-destructive text-destructive-foreground"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <WebRequestForm
        collectionId={collectionId}
        webhook={editingWebhook}
        open={isFormOpen}
        onOpenChange={handleFormClose}
      />
    </div>
  );
};
