import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle2, Copy, Clock } from 'lucide-react';
import { describeCronExpression, CRON_EXAMPLES, type CronDescription } from '@/lib/cron-utils';
import { cn } from '@/lib/utils';
import { FadeIn } from '@/components/motion/fade-in';
import { CronInput } from '@/components/cron-input';
import { useAuthStore } from '@/stores/auth-store';
import { useOAuthLogin } from '@/hooks/use-auth';

export default function CronBuilderPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialValue = searchParams.get('value') || '';
  const returnUrl = searchParams.get('return') || '/dashboard';

  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { mutate: loginWithOAuth, isPending: isLoginPending, variables } = useOAuthLogin();

  const [cronExpression, setCronExpression] = useState(initialValue);
  const [description, setDescription] = useState<CronDescription | null>(null);
  const [copied, setCopied] = useState(false);

  const handleOAuthLogin = (provider: string) => {
    loginWithOAuth(provider);
  };

  useEffect(() => {
    if (initialValue) {
      setCronExpression(initialValue);
    }
  }, [initialValue]);

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
    if (description?.isValid) {
      // Store the selected expression in localStorage and navigate back
      if (returnUrl.includes('add-new') || returnUrl.includes('edit')) {
        sessionStorage.setItem('selectedCronExpression', cronExpression);
        navigate(returnUrl);
      } else {
        // For other cases, pass via URL
        const url = new URL(returnUrl, window.location.origin);
        url.searchParams.set('cron', cronExpression);
        navigate(url.pathname + url.search);
      }
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(cronExpression);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-background p-6 pl-32">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <FadeIn>
          <div className="mb-6">
            <div className="flex items-center gap-2">
              <Clock className="h-6 w-6 text-primary" />
              <h1 className="text-3xl font-bold">Cron Expression Builder</h1>
            </div>
            <p className="text-muted-foreground text-sm mt-2">
              Build and validate cron expressions. Use the custom input fields below or enter a
              6-field cron expression manually.
            </p>
          </div>
        </FadeIn>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Input and Examples */}
          <div className="lg:col-span-2 space-y-6">
            {/* Custom Input Section */}
            <FadeIn delay={0.1}>
              <Card className="border">
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-medium">Build Cron Expression</Label>
                    </div>
                    <CronInput value={cronExpression} onChange={handleExpressionChange} />
                  </div>
                  {/* Validation Status */}
                  {cronExpression.trim() && description && (
                    <FadeIn delay={0.2}>
                      <Card
                        className={cn(
                          'border mt-4',
                          description.isValid
                            ? 'border-green-500/20 bg-green-500/5'
                            : 'border-destructive/50 bg-destructive/5'
                        )}
                      >
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="flex-1 space-y-3">
                              {description.isValid ? (
                                <>
                                  <div>
                                    <div className="flex items-center justify-between mb-1">
                                      <div className="flex items-center gap-2">
                                        <CheckCircle2 className="h-6 w-6 text-green-500 shrink-0 mt-0.5" />
                                        <p className="text-sm font-medium text-green-500">
                                          Valid Expression
                                        </p>
                                      </div>
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
                                    <p className="text-base font-semibold text-foreground">
                                      {description.description}
                                    </p>
                                  </div>
                                  {description.nextRuns.length > 0 && (
                                    <div>
                                      <p className="text-sm font-medium text-muted-foreground mb-2">
                                        Next runs (approximate):
                                      </p>
                                      <div className="flex flex-wrap gap-2">
                                        {description.nextRuns.map((run, idx) => (
                                          <Badge key={idx} variant="outline" className="text-xs">
                                            {run}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </>
                              ) : (
                                <div>
                                  <p className="text-sm font-medium text-muted-foreground mb-1">
                                    Error
                                  </p>
                                  <p className="text-base font-semibold text-destructive">
                                    Invalid Expression
                                  </p>
                                  {description.error && (
                                    <p className="text-sm text-destructive mt-2">
                                      {description.error}
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </FadeIn>
                  )}
                </CardContent>
              </Card>
            </FadeIn>

            {/* Examples Section */}
            <FadeIn delay={0.3}>
              <Card className="border">
                <CardContent className="p-6">
                  <Label className="text-sm font-medium mb-4 block">Quick Examples</Label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {CRON_EXAMPLES.map((example, idx) => (
                      <Card
                        key={idx}
                        className="border cursor-pointer hover:border-primary/50 hover:bg-accent/50 transition-colors"
                        onClick={() => handleExampleClick(example.expression)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-mono text-foreground mb-1.5 font-semibold">
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
                </CardContent>
              </Card>
            </FadeIn>

            {/* Action Buttons for Authenticated Users */}
            {isAuthenticated && (
              <FadeIn delay={0.4}>
                <div className="flex justify-end gap-3 pt-1">
                  <Button type="button" variant="outline" onClick={() => navigate(returnUrl)}>
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    onClick={handleUseExpression}
                    disabled={!description?.isValid}
                    className="min-w-[160px]"
                  >
                    Use This Expression
                  </Button>
                </div>
              </FadeIn>
            )}
          </div>

          {/* Right Column - Documentation (Sticky) */}
          <div className="lg:col-span-1">
            {/* Action Buttons or Login CTA */}
            <FadeIn delay={0.5}>
              {!isAuthenticated && (
                <Card className="border-2 border-primary/20 bg-primary/5 overflow-hidden mb-6">
                  <CardContent className="p-5">
                    <div className="space-y-4">
                      <div className="flex items-start gap-3">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-base font-semibold mb-1.5">
                            Sign in to schedule webhook triggers
                          </h3>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            Create an account or sign in to save and use your cron expressions. Get
                            started with scheduled webhook triggers in seconds.
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col gap-2 pt-2">
                        <Button
                          variant="outline"
                          size="default"
                          onClick={() => handleOAuthLogin('google')}
                          disabled={isLoginPending}
                          className="w-full gap-2"
                        >
                          <svg
                            className="h-4 w-4 shrink-0"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                              fill="#4285F4"
                            />
                            <path
                              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                              fill="#34A853"
                            />
                            <path
                              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                              fill="#FBBC05"
                            />
                            <path
                              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                              fill="#EA4335"
                            />
                          </svg>
                          <span className="truncate">
                            {isLoginPending && variables === 'google'
                              ? 'Signing in...'
                              : 'Continue with Google'}
                          </span>
                        </Button>
                        <Button
                          variant="outline"
                          size="default"
                          onClick={() => handleOAuthLogin('github')}
                          disabled={isLoginPending}
                          className="w-full gap-2"
                        >
                          <svg
                            className="h-4 w-4 shrink-0"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <path
                              fillRule="evenodd"
                              clipRule="evenodd"
                              d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                            />
                          </svg>
                          <span className="truncate">
                            {isLoginPending && variables === 'github'
                              ? 'Signing in...'
                              : 'Continue with GitHub'}
                          </span>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </FadeIn>

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
  );
}
