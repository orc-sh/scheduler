import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/routers/guards/protected-route';
import PublicRoute from '@/routers/guards/public-route';
import LoginPage from '@/pages/login';
import AuthCallbackPage from '@/pages/auth-callback';
import DashboardPage from '@/pages/dashboard';
import NotFoundPage from '@/pages/not-found';

export const AppRouter = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
      </Route>

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>

      {/* Redirect root to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Catch all - 404 Not Found */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
