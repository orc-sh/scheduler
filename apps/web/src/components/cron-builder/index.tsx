import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, CheckCircle2, Copy, Clock } from 'lucide-react';
import { describeCronExpression, CRON_EXAMPLES, type CronDescription } from '@/lib/cron-utils';
import { cn } from '@/lib/utils';

interface CronBuilderProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  value?: string;
  onSelect?: (cron: string) => void;
}

export function CronBuilder({ open, onOpenChange, value = '', onSelect }: CronBuilderProps) {
  const [cronExpression, setCronExpression] = useState(value);
  const [description, setDescription] = useState<CronDescription | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (open && value) {
      setCronExpression(value);
    }
  }, [open, value]);

  useEffect(() => {
    if (cronExpression.trim()) {
      const desc = describeCronExpression(cronExpression);
      setDescription(desc);
    } else {
      setDescription(null);
    }
  }, [cronExpression]);

  const handleExpressionChange = (newExpression: string) => {
    setCronExpression(newExpression);
  };

  const handleExampleClick = (example: string) => {
    setCronExpression(example);
  };

  const handleUseExpression = () => {
    if (description?.isValid && onSelect) {
      onSelect(cronExpression);
      onOpenChange(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(cronExpression);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            <DialogTitle>Cron Expression Builder</DialogTitle>
          </div>
          <DialogDescription>
            Build and validate cron expressions. Enter a 5-field cron expression to see what it
            means.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Input Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="cron-input" className="text-sm font-medium">
                Cron Expression
              </Label>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-7 text-xs"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3 mr-1" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </div>
            <Input
              id="cron-input"
              value={cronExpression}
              onChange={(e) => handleExpressionChange(e.target.value)}
              placeholder="* * * * *"
              className="font-mono text-sm h-10"
            />
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="font-mono">minute</span>
              <span>hour</span>
              <span>day</span>
              <span>month</span>
              <span>weekday</span>
            </div>
          </div>

          {/* Validation Status */}
          {cronExpression.trim() && description && (
            <Card
              className={cn(
                'border',
                description.isValid ? 'border-green-500/20' : 'border-destructive/50'
              )}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  {description.isValid ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 space-y-2">
                    {description.isValid ? (
                      <>
                        <p className="text-sm font-medium text-foreground">
                          {description.description}
                        </p>
                        {description.nextRuns.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Next runs:</p>
                            <div className="flex flex-wrap gap-1">
                              {description.nextRuns.slice(0, 3).map((run, idx) => (
                                <Badge key={idx} variant="outline" className="text-[10px]">
                                  {run}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div>
                        <p className="text-sm font-medium text-destructive">Invalid Expression</p>
                        {description.error && (
                          <p className="text-xs text-destructive mt-1">{description.error}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Examples Section */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Quick Examples</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {CRON_EXAMPLES.map((example, idx) => (
                <Card
                  key={idx}
                  className="border cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => handleExampleClick(example.expression)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-mono text-foreground mb-1">
                          {example.expression}
                        </p>
                        <p className="text-xs text-muted-foreground">{example.description}</p>
                      </div>
                      <Badge variant="outline" className="text-[10px] shrink-0">
                        {example.label}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Help Section */}
          <Card className="border">
            <CardContent className="p-4">
              <h4 className="text-sm font-medium mb-2">Cron Expression Format</h4>
              <div className="space-y-2 text-xs text-muted-foreground">
                <p>
                  A cron expression consists of 5 fields separated by spaces:
                  <code className="ml-1 px-1 py-0.5 bg-muted rounded font-mono">
                    minute hour day month weekday
                  </code>
                </p>
                <div className="space-y-1 mt-3">
                  <p>
                    <strong className="text-foreground">Special characters:</strong>
                  </p>
                  <ul className="list-disc list-inside space-y-0.5 ml-2">
                    <li>
                      <code className="px-1 py-0.5 bg-muted rounded font-mono">*</code> - Any value
                    </li>
                    <li>
                      <code className="px-1 py-0.5 bg-muted rounded font-mono">,</code> - Value list
                      separator
                    </li>
                    <li>
                      <code className="px-1 py-0.5 bg-muted rounded font-mono">-</code> - Range of
                      values
                    </li>
                    <li>
                      <code className="px-1 py-0.5 bg-muted rounded font-mono">/</code> - Step
                      values
                    </li>
                  </ul>
                </div>
                <div className="space-y-1 mt-3">
                  <p>
                    <strong className="text-foreground">Field ranges:</strong>
                  </p>
                  <ul className="list-disc list-inside space-y-0.5 ml-2">
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

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            <Button type="button" onClick={handleUseExpression} disabled={!description?.isValid}>
              Use This Expression
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
