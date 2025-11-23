import { useCurrentUser } from '@/hooks/use-auth';
import { FadeIn } from '@/components/motion/fade-in';

const DashboardPage = () => {
  // Fetch current user data
  useCurrentUser();

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto space-y-8">
        <FadeIn>
          <h1 className="text-4xl font-bold">Dashboard</h1>
        </FadeIn>
      </div>
    </div>
  );
};

export default DashboardPage;
