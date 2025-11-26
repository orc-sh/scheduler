import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { LogoIcon } from '@/components/logo';
import { useForgotPassword } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const ForgotPasswordPage = () => {
  const { mutate: forgotPassword, isPending, isSuccess } = useForgotPassword();
  const [email, setEmail] = useState('');

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!email || isPending) return;
    forgotPassword({ email });
  };

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

            <h1 className="mb-1 mt-4 text-xl font-semibold">
              {isSuccess ? 'Check Your Email' : 'Recover Password'}
            </h1>
            <p className="text-sm">
              {isSuccess
                ? 'We sent you a link to reset your password'
                : 'Enter your email to receive a reset link'}
            </p>
          </div>

          {!isSuccess ? (
            <>
              <div className="mt-6 space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email" className="block text-sm">
                    Email
                  </Label>
                  <Input
                    type="email"
                    required
                    name="email"
                    id="email"
                    autoComplete="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isPending}
                  />
                </div>

                <Button className="w-full" type="submit" disabled={isPending}>
                  {isPending ? 'Sending...' : 'Send Reset Link'}
                </Button>
              </div>

              <div className="mt-6 text-center">
                <p className="text-muted-foreground text-sm">
                  We'll send you a link to reset your password.
                </p>
              </div>
            </>
          ) : (
            <div className="mt-6 text-center">
              <p className="text-muted-foreground text-sm">
                We've sent password reset instructions to{' '}
                <span className="font-medium text-foreground">{email}</span>. Please check your
                inbox and click the link to reset your password.
              </p>
            </div>
          )}
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

export default ForgotPasswordPage;
