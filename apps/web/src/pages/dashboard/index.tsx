import { useNavigate } from 'react-router-dom';
import { useCurrentUser } from '@/hooks/use-auth';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent } from '@/components/ui/card';
import { Globe, CalendarClock, Package, Hammer } from 'lucide-react';

const DashboardPage = () => {
  const navigate = useNavigate();

  // Fetch current user data
  useCurrentUser();

  const modules = [
    {
      icon: Globe,
      title: 'URLs',
      description: 'Create and manage webhook-like URL endpoints',
      path: '/urls',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      icon: CalendarClock,
      title: 'Schedules',
      description: 'Manage scheduled webhook endpoints',
      path: '/schedules',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      icon: Hammer,
      title: 'Cron Builder',
      description: 'Build and test cron expressions',
      path: '/cron-builder',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
  ];

  return (
    <div className="min-h-screen bg-background p-8 pl-32 flex flex-col justify-center items-center">
      <div className="container mx-auto max-w-6xl">
        <FadeIn>
          {/* Welcome Header */}
          <div className="mb-10">
            <h1 className="text-3xl font-bold tracking-tight mb-2">
              Welcome to{' '}
              <span className="text-primary text-4xl font-bold font-poppins">hookiee</span>.site
            </h1>
            <p className="text-sm text-muted-foreground max-w-2xl">
              Manage your endpoints, schedules, and cron expressions all in one place.
            </p>
          </div>

          {/* Module Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {modules.map((module) => {
              const Icon = module.icon;
              return (
                <Card
                  key={module.path}
                  className="rounded-lg border-border/50 cursor-pointer transition-all hover:border-border hover:shadow-sm group overflow-hidden"
                  onClick={() => navigate(module.path)}
                >
                  <CardContent className="p-4">
                    <div className="flex gap-3 items-center">
                      <div className={`rounded-md p-3 ${module.bgColor}`}>
                        <Icon className={`h-4 w-4 ${module.color}`} />
                      </div>
                      <div className="space-y-1">
                        <h3 className="text-base font-semibold leading-tight text-foreground">
                          {module.title}
                        </h3>
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                          {module.description}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </FadeIn>
      </div>
    </div>
  );
};

export default DashboardPage;
