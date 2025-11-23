import { BrowserRouter, useLocation } from 'react-router-dom';
import { QueryProvider } from '@/providers/query-provider';
import { AppRouter } from '@/routers';
import FloatingNavbar from '@/components/layout/floating-navbar';

const AppContent = () => {
  const location = useLocation();

  // Hide navbar on public routes
  const publicRoutes = ['/login', '/auth/callback'];
  const shouldShowNavbar = !publicRoutes.includes(location.pathname);

  return (
    <>
      {shouldShowNavbar && <FloatingNavbar />}
      <AppRouter />
    </>
  );
};

function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryProvider>
  );
}

export default App;
