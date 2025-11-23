import { useAuthStore } from '@/stores/auth-store';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { User } from 'lucide-react';

const ProfilePage = () => {
  const user = useAuthStore((state) => state.user);

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto space-y-8">
        <FadeIn>
          <h1 className="text-4xl font-bold">Profile</h1>
        </FadeIn>

        <FadeIn delay={0.2} className="max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Your Profile
              </CardTitle>
              <CardDescription>View and edit your profile information</CardDescription>
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
                          className="h-16 w-16 rounded-full"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </div>
  );
};

export default ProfilePage;
