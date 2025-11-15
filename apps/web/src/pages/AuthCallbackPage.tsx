import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

const AuthCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { handleOAuthCallback } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      // Get authorization code from URL
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      if (errorParam) {
        setError(errorDescription || 'Authentication failed');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      if (!code) {
        setError('No authorization code received');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      try {
        // Exchange code for tokens
        await handleOAuthCallback(code);

        // Redirect to dashboard/home on success
        navigate('/dashboard');
      } catch (err) {
        console.error('Error processing OAuth callback:', err);
        setError('Failed to complete authentication. Please try again.');
        setTimeout(() => navigate('/login'), 3000);
      }
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
