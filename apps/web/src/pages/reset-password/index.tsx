import { type FormEvent, useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { LogoIcon } from '@/components/logo';
import { useResetPassword } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { mutate: resetPassword, isPending, isSuccess, isError, error } = useResetPassword();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [token, setToken] = useState('');

  useEffect(() => {
    // Supabase sends the token as a hash fragment (#access_token=...)
    // We need to extract it from the hash and convert to query parameter
    const hash = window.location.hash;
    let urlToken = '';

    if (hash) {
      // Extract access_token from hash fragment (format: #access_token=xxx&type=recovery)
      const hashParams = new URLSearchParams(hash.substring(1));
      urlToken = hashParams.get('access_token') || '';
    }
    setToken(urlToken);
  }, [searchParams]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!password || !confirmPassword || !token || isPending) return;
    if (password !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please make sure both passwords are the same.',
        variant: 'destructive',
      });
      return;
    }
    resetPassword(
      { password, token },
      {
        onSuccess: () => {
          toast({
            title: 'Password Reset',
            description: 'Your password has been successfully reset. Please sign in.',
          });
          setTimeout(() => {
            navigate('/sign-in', { replace: true });
          }, 2000);
        },
        onError: (err) => {
          toast({
            title: 'Reset Failed',
            description:
              err.message || 'Failed to reset password. The link might be expired or invalid.',
            variant: 'destructive',
          });
        },
      }
    );
  };

  if (isSuccess) {
    return (
      <section className="fixed inset-0 flex items-center justify-center bg-zinc-50 px-4 dark:bg-transparent overflow-hidden">
        <div className="bg-muted m-auto h-fit w-full max-w-sm overflow-hidden rounded-[calc(var(--radius)+.125rem)] border shadow-md shadow-zinc-950/5 dark:[--color-muted:var(--color-zinc-900)]">
          <div className="bg-card -m-px rounded-[calc(var(--radius)+.125rem)] border p-8 pb-6">
            <div className="text-center space-y-6">
              <Link to="/" aria-label="go home" className="mx-auto block w-fit">
                <LogoIcon />
              </Link>

              <div className="space-y-3">
                <h1 className="text-2xl font-semibold">Password Reset Successful</h1>
                <p className="text-sm text-muted-foreground">
                  Your password has been reset. You can now sign in with your new password.
                </p>
              </div>

              <div className="pt-4">
                <Button asChild className="w-full">
                  <Link to="/sign-in">Continue to Sign In</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (!token) {
    return (
      <section className="fixed inset-0 flex items-center justify-center bg-zinc-50 px-4 dark:bg-transparent overflow-hidden">
        <div className="bg-muted m-auto h-fit w-full max-w-sm overflow-hidden rounded-[calc(var(--radius)+.125rem)] border shadow-md shadow-zinc-950/5 dark:[--color-muted:var(--color-zinc-900)]">
          <div className="bg-card -m-px rounded-[calc(var(--radius)+.125rem)] border p-8 pb-6">
            <div className="text-center space-y-6">
              <Link to="/" aria-label="go home" className="mx-auto block w-fit">
                <LogoIcon />
              </Link>

              <div className="space-y-3">
                <h1 className="text-xl font-semibold">Invalid Reset Link</h1>
                <p className="text-sm text-muted-foreground">
                  This password reset link is invalid or has expired. Please request a new one.
                </p>
              </div>

              <div className="pt-4">
                <Button asChild variant="outline" className="w-full">
                  <Link to="/forgot-password">Request New Reset Link</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="fixed inset-0 flex items-center justify-center bg-zinc-50 px-4 dark:bg-transparent overflow-hidden">
      <form
        onSubmit={handleSubmit}
        className="bg-muted m-auto h-fit w-full max-w-sm overflow-hidden rounded-[calc(var(--radius)+.125rem)] border shadow-md shadow-zinc-950/5 dark:[--color-muted:var(--color-zinc-900)]"
      >
        <div className="bg-card -m-px rounded-[calc(var(--radius)+.125rem)] border p-8 pb-6">
          <div className="text-center">
            <Link to="/" aria-label="go home" className="mx-auto block w-fit">
              <LogoIcon />
            </Link>

            <h1 className="mb-1 mt-4 text-xl font-semibold">Reset Password</h1>
            <p className="text-sm">Enter your new password below</p>
          </div>

          {isError && (
            <div className="mt-4 rounded-lg border border-destructive/50 bg-destructive/5 p-3 text-sm text-destructive">
              {error instanceof Error
                ? error.message
                : 'Failed to reset password. Please try again.'}
            </div>
          )}

          <div className="mt-6 space-y-6">
            <div className="space-y-2">
              <Label htmlFor="password" className="block text-sm">
                New Password
              </Label>
              <Input
                type="password"
                required
                name="password"
                id="password"
                autoComplete="new-password"
                placeholder="Enter new password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="block text-sm">
                Confirm Password
              </Label>
              <Input
                type="password"
                required
                name="confirmPassword"
                id="confirmPassword"
                autoComplete="new-password"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={isPending}
              />
            </div>

            <Button className="w-full" type="submit" disabled={isPending}>
              {isPending ? 'Resetting Password...' : 'Reset Password'}
            </Button>
          </div>
        </div>

        <div className="p-3">
          <p className="text-accent-foreground text-center text-sm">
            Remembered your password?
            <Button asChild variant="link" className="px-2">
              <Link to="/sign-in">Log in</Link>
            </Button>
          </p>
        </div>
      </form>
    </section>
  );
};

export default ResetPasswordPage;
