import { BrowserRouter } from 'react-router-dom';
import { QueryProvider } from '@/providers/query-provider';
import { AppRouter } from '@/routers';

function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </QueryProvider>
  );
}

export default App;
