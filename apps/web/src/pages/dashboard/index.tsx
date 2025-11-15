import { useCurrentUser, useLogout } from '@/hooks/use-auth';
import { useAuthStore } from '@/stores/auth-store';
import { FadeIn } from '@/components/motion/fade-in';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LogOut, User } from 'lucide-react';

const DashboardPage = () => {
  const user = useAuthStore((state) => state.user);
  const { mutate: logout } = useLogout();

  // Fetch current user data
  useCurrentUser();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="container mx-auto space-y-8">
        <div className="flex justify-between items-center">
          <FadeIn>
            <h1 className="text-4xl font-bold">Dashboard</h1>
          </FadeIn>
          <FadeIn delay={0.1}>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </FadeIn>
        </div>

        <FadeIn delay={0.2} className="max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Welcome Back!
              </CardTitle>
              <CardDescription>You are successfully authenticated</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Email</p>
                <p className="text-base font-semibold">{user?.email}</p>
              </div>

              {user?.user_metadata && Object.keys(user.user_metadata).length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    Profile Information
                  </p>
                  <div className="space-y-2">
                    {user.user_metadata.full_name && (
                      <div>
                        <p className="text-sm text-muted-foreground">Name</p>
                        <p className="text-base">{user.user_metadata.full_name}</p>
                      </div>
                    )}
                    {user.user_metadata.avatar_url && (
                      <div className="flex items-center gap-3">
                        <img
                          src={user.user_metadata.avatar_url}
                          alt="Avatar"
                          className="h-12 w-12 rounded-full"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  User ID: <code className="text-xs bg-muted px-2 py-1 rounded">{user?.id}</code>
                </p>
              </div>
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </div>
  );
};

export default DashboardPage;
