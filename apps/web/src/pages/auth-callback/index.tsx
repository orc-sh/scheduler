import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useOAuthCallback } from '@/hooks/use-auth';
import { useAuthStore } from '@/stores/auth-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

const AuthCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { mutate: handleOAuthCallback } = useOAuthCallback();
  const [error, setError] = useState<string | null>(null);
  const hasProcessedCallback = useRef(false);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Navigate to dashboard once authentication is confirmed
  useEffect(() => {
    if (isAuthenticated && hasProcessedCallback.current && !error) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate, error]);

  useEffect(() => {
    const processCallback = () => {
      // Prevent duplicate processing
      if (hasProcessedCallback.current) {
        return;
      }

      // Get authorization code from URL
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      if (errorParam) {
        setError(errorDescription || 'Authentication failed');
        setTimeout(() => navigate('/sign-in'), 3000);
        return;
      }

      if (!code) {
        setError('No authorization code received');
        setTimeout(() => navigate('/sign-in'), 3000);
        return;
      }

      // Mark as processing to prevent duplicate calls
      hasProcessedCallback.current = true;

      // Exchange code for tokens
      handleOAuthCallback(code, {
        onSuccess: () => {
          // Navigation will happen in the other useEffect when isAuthenticated becomes true
          console.log('OAuth callback successful, authentication state updating...');
        },
        onError: (err) => {
          console.error('Error processing OAuth callback:', err);
          setError('Failed to complete authentication. Please try again.');
          setTimeout(() => navigate('/sign-in'), 3000);
        },
      });
    };

    processCallback();
  }, [searchParams, handleOAuthCallback, navigate]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>{error ? 'Authentication Failed' : 'Completing Sign In...'}</CardTitle>
          <CardDescription>
            {error
              ? 'Redirecting you back to login...'
              : 'Please wait while we complete your authentication'}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center space-y-4">
          {error ? (
            <div className="text-destructive text-center">
              <p>{error}</p>
            </div>
          ) : (
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AuthCallbackPage;
