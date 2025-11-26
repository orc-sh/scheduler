import { Link } from 'react-router-dom';
import { LogoIcon } from '@/components/logo';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

const SignupSuccessPage = () => {
  return (
    <section className="flex min-h-screen bg-zinc-50 px-4 py-16 md:py-32 dark:bg-transparent">
      <div className="m-auto h-fit w-full max-w-md">
        <Card className="bg-muted overflow-hidden rounded-[calc(var(--radius)+.125rem)] border shadow-md shadow-zinc-950/5 dark:[--color-muted:var(--color-zinc-900)]">
          <div className="bg-card -m-px rounded-[calc(var(--radius)+.125rem)] border p-8 pb-6">
            <div className="text-center space-y-6">
              <Link to="/" aria-label="go home" className="mx-auto block w-fit">
                <LogoIcon />
              </Link>

              <div className="space-y-3">
                <h1 className="text-2xl font-semibold">Account Created Successfully</h1>
                <p className="text-sm text-muted-foreground">
                  We've sent a confirmation email to your inbox. Please check your email and click
                  the confirmation link to activate your account.
                </p>
              </div>

              <div className="pt-4">
                <Button asChild className="w-full">
                  <Link to="/sign-in">Continue to Sign In</Link>
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
};

export default SignupSuccessPage;
