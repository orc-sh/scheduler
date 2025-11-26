import { BrowserRouter, useLocation } from 'react-router-dom';
import { QueryProvider } from '@/providers/query-provider';
import { ThemeProvider } from '@/providers/theme-provider';
import { AppRouter } from '@/routers';
import FloatingNavbar from '@/components/layout/floating-navbar';
import { Toaster } from '@/components/ui/sonner';

const AppContent = () => {
  const location = useLocation();

  // Hide navbar on public routes
  const publicRoutes = [
    '/sign-in',
    '/sign-up',
    '/forgot-password',
    '/reset-password',
    '/auth/callback',
  ];
  const shouldShowNavbar = !publicRoutes.includes(location.pathname);

  return (
    <>
      {shouldShowNavbar && <FloatingNavbar />}
      <AppRouter />
      <Toaster />
    </>
  );
};

function App() {
  return (
    <ThemeProvider>
      <QueryProvider>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </QueryProvider>
    </ThemeProvider>
  );
}

export default App;
