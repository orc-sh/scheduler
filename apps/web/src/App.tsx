import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

function App() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="container mx-auto">
        <h1 className="text-4xl font-bold mb-8">Welcome to shadcn/ui</h1>
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Setup Complete!</CardTitle>
            <CardDescription>shadcn/ui is now installed and ready to use.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button>Primary Button</Button>
              <Button variant="outline">Outline Button</Button>
              <Button variant="secondary">Secondary</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;
