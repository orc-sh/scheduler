import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/routers/guards/protected-route';
import PublicRoute from '@/routers/guards/public-route';
import LoginPage from '@/pages/login';
import SignUpPage from '@/pages/sign-up';
import ForgotPasswordPage from '@/pages/forgot-password';
import ResetPasswordPage from '@/pages/reset-password';
import AuthCallbackPage from '@/pages/auth-callback';
import CronBuilderPage from '@/pages/cron-builder';
import DashboardPage from '@/pages/dashboard';
import UrlsPage from '@/pages/urls';
import SchedulesPage from '@/pages/schedules';
import AddNewPage from '@/pages/add-new';
import EditWebhookPage from '@/pages/edit';
import WebhookDetailsPage from '@/pages/webhook-details';
import UrlDetailsPage from '@/pages/url-details';
import NotificationsPage from '@/pages/notifications';
import ProfilePage from '@/pages/profile';
import BillingCallbackPage from '@/pages/billing-callback';
import NotFoundPage from '@/pages/not-found';

export const AppRouter = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<PublicRoute />}>
        <Route path="/sign-in" element={<LoginPage />} />
        <Route path="/sign-up" element={<SignUpPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/billing/callback" element={<BillingCallbackPage />} />
      </Route>

      {/* Public cron builder (no auth required) */}
      <Route path="/cron-builder" element={<CronBuilderPage />} />

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/endpoints" element={<UrlsPage />} />
        <Route path="/endpoints/:id" element={<UrlDetailsPage />} />
        <Route path="/schedules" element={<SchedulesPage />} />
        <Route path="/schedules/new" element={<AddNewPage />} />
        <Route path="/schedules/:id" element={<WebhookDetailsPage />} />
        <Route path="/edit/:id" element={<EditWebhookPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* Catch all - 404 Not Found */}
      <Route path="/404" element={<NotFoundPage />} />

      {/* Redirect root to dashboard */}
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
};
