import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/routers/guards/protected-route';
import PublicRoute from '@/routers/guards/public-route';
import LoginPage from '@/pages/login';
import AuthCallbackPage from '@/pages/auth-callback';
import CronBuilderPage from '@/pages/cron-builder';
import DashboardPage from '@/pages/dashboard';
import SchedulesPage from '@/pages/schedules';
import AddNewPage from '@/pages/add-new';
import EditWebhookPage from '@/pages/edit';
import WebhookDetailsPage from '@/pages/webhook-details';
import UrlDetailsPage from '@/pages/url-details';
import NotificationsPage from '@/pages/notifications';
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

      {/* Public cron builder (no auth required) */}
      <Route path="/cron-builder" element={<CronBuilderPage />} />

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/schedules" element={<SchedulesPage />} />
        <Route path="/add-new" element={<AddNewPage />} />
        <Route path="/webhooks/:id" element={<WebhookDetailsPage />} />
        <Route path="/urls/:id" element={<UrlDetailsPage />} />
        <Route path="/edit/:id" element={<EditWebhookPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* Redirect root to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Catch all - 404 Not Found */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
