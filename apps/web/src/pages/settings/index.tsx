import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings } from 'lucide-react';

const SettingsPage = () => {
  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto space-y-8">
        <FadeIn>
          <h1 className="text-4xl font-bold">Settings</h1>
        </FadeIn>

        <FadeIn delay={0.2} className="max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Application Settings
              </CardTitle>
              <CardDescription>Manage your preferences and account settings</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                This is a placeholder for the Settings page. You can add your settings options here.
              </p>
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </div>
  );
};

export default SettingsPage;
