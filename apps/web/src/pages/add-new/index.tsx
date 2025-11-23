import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PlusCircle } from 'lucide-react';

const AddNewPage = () => {
  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto space-y-8">
        <FadeIn>
          <h1 className="text-4xl font-bold">Add New</h1>
        </FadeIn>

        <FadeIn delay={0.2} className="max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PlusCircle className="h-5 w-5" />
                Create New Item
              </CardTitle>
              <CardDescription>Add a new event, task, or schedule</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                This is a placeholder for the Add New page. You can add your form or content here.
              </p>
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </div>
  );
};

export default AddNewPage;
