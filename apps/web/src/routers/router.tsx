import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/routers/guards/protected-route';
import PublicRoute from '@/routers/guards/public-route';
import LoginPage from '@/pages/login';
import AuthCallbackPage from '@/pages/auth-callback';
import DashboardPage from '@/pages/dashboard';
import AddNewPage from '@/pages/add-new';
import EditWebhookPage from '@/pages/edit';
import WebhookDetailsPage from '@/pages/webhook-details';
import SettingsPage from '@/pages/settings';
import ProfilePage from '@/pages/profile';
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
        <Route path="/add-new" element={<AddNewPage />} />
        <Route path="/webhooks/:id" element={<WebhookDetailsPage />} />
        <Route path="/edit/:id" element={<EditWebhookPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* Redirect root to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Catch all - 404 Not Found */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
