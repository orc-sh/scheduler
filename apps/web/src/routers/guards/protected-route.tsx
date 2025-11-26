import { Navigate, Outlet } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/auth-store';
import { useCurrentUser } from '@/hooks/use-auth';
import { Loader2 } from 'lucide-react';
import { clearTokens } from '@/lib/api';

const ProtectedRoute: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const { isPending } = useCurrentUser();

  // Clear invalid auth state (user exists but no valid tokens)
  useEffect(() => {
    if (!accessToken || !refreshToken) {
      clearTokens();
      useAuthStore.getState().clearAuth();
    }
  }, [accessToken, refreshToken]);

  if (isAuthenticated && isPending) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAuthenticated || !accessToken || !refreshToken) {
    return <Navigate to="/sign-in" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
