import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateCollection } from '@/hooks/use-load-tests';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Gauge, Zap, ChevronDown } from 'lucide-react';
import type { CreateCollectionRequest } from '@/types/load-test.types';

const NewLoadTestPage = () => {
  const navigate = useNavigate();
  const createConfig = useCreateCollection();

  const [formData, setFormData] = useState<Partial<CreateCollectionRequest>>({
    name: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Prepare submit data for collection (only name)
      const submitData: CreateCollectionRequest = {
        name: formData.name || '',
      };

      const result = await createConfig.mutateAsync(submitData);
      navigate(`/load-tests/${result.id}`);
    } catch (error) {
      // Error handled by hook
    }
  };

  return (
    <div className="min-h-screen bg-background p-6 pl-24">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <FadeIn>
          <div className="mb-6">
            <div className="flex items-center gap-2">
              <Gauge className="h-6 w-6 text-primary" />
              <h1 className="text-3xl font-bold">Create Collection</h1>
            </div>
            <p className="text-muted-foreground text-sm mt-2">
              Create a new webhook collection. You'll add web requests on the next page.
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Form */}
          <div className="lg:col-span-2 space-y-5">
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Basic Configuration Section */}
              <FadeIn delay={0.1}>
                <Card className="border rounded-lg">
                  <button
                    type="button"
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-accent/50 transition-colors rounded-t-lg"
                    onClick={() => {}}
                  >
                    <div className="flex items-center gap-2 text-lg font-semibold">
                      <Zap className="h-4 w-4 text-primary" />
                      Basic Configuration
                    </div>
                    <ChevronDown className="h-4 w-4 shrink-0 transition-transform duration-200" />
                  </button>
                  <CardContent className="px-6 pb-6">
                    <div className="space-y-4 pt-2">
                      {/* Test Name */}
                      <div className="space-y-1.5">
                        <Label htmlFor="name" className="text-xs font-medium">
                          Name
                        </Label>
                        <Input
                          id="name"
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          placeholder="e.g., API Collection (optional)"
                          className="h-9"
                        />
                        <p className="text-xs text-muted-foreground">
                          You can add a name later or leave it blank
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </FadeIn>

              {/* Submit Button */}
              <FadeIn delay={0.3}>
                <div className="flex gap-3 justify-end pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate('/load-tests')}
                    disabled={createConfig.isPending}
                    className="h-9"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createConfig.isPending} className="h-9">
                    {createConfig.isPending ? (
                      <>
                        <div className="h-3.5 w-3.5 border-2 border-background border-t-transparent rounded-full animate-spin mr-2" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Gauge className="h-3.5 w-3.5 mr-2" />
                        Create Collection
                      </>
                    )}
                  </Button>
                </div>
              </FadeIn>
            </form>
          </div>

          {/* Right Column - Information Box (Sticky) */}
          <div className="lg:col-span-1">
            <FadeIn delay={0.4}>
              <Card className="border sticky top-6">
                <CardContent className="p-6">
                  <h4 className="text-sm font-semibold mb-3">About Collections</h4>
                  <div className="space-y-3 text-sm text-muted-foreground">
                    <p>
                      Collections are groups of web requests that you can test together. Create a
                      collection, add multiple web requests, and then run load tests with different
                      execution parameters.
                    </p>
                    <div className="space-y-2 mt-4">
                      <p>
                        <strong className="text-foreground">Web Requests:</strong>
                      </p>
                      <p className="text-xs">
                        Add multiple HTTP requests with different methods, URLs, headers, and body
                        templates. They will be executed in the order you specify.
                      </p>
                    </div>
                    <div className="space-y-2 mt-4">
                      <p>
                        <strong className="text-foreground">Running Tests:</strong>
                      </p>
                      <p className="text-xs">
                        When you run a test, you'll specify execution parameters like concurrent
                        threads, duration, and rate limits. These can be different for each test
                        run.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </FadeIn>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewLoadTestPage;
