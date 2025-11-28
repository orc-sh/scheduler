import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FadeIn } from '@/components/motion/fade-in';
import { Home, ArrowLeft } from 'lucide-react';

const NotFoundPage = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <FadeIn className="w-full max-w-md">
        <Card>
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto mb-4 text-6xl font-bold text-muted-foreground">404</div>
            <CardTitle className="text-3xl font-bold">Page Not Found</CardTitle>
            <CardDescription>
              The page you're looking for doesn't exist or has been moved.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button variant="default" size="lg" className="w-full" onClick={handleGoHome}>
              <Home className="mr-2 h-5 w-5" />
              Go to Dashboard
            </Button>
            <Button variant="outline" size="lg" className="w-full" onClick={handleGoBack}>
              <ArrowLeft className="mr-2 h-5 w-5" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </FadeIn>
    </div>
  );
};

export default NotFoundPage;
