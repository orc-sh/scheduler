import { Home, PlusCircle, Settings, LogOut } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useAuthStore } from '@/stores/auth-store';
import { useLogout } from '@/hooks/use-auth';
import { cn } from '@/lib/utils';

const FloatingNavbar = () => {
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const { mutate: logout } = useLogout();

  const navItems = [
    {
      icon: Home,
      label: 'Home',
      path: '/dashboard',
    },
    {
      icon: PlusCircle,
      label: 'Add New',
      path: '/add-new',
    },
    {
      icon: Settings,
      label: 'Settings',
      path: '/settings',
    },
  ];

  const avatarUrl = user?.user_metadata?.avatar_url;
  const userEmail = user?.email || '';
  const initials = userEmail.slice(0, 2).toUpperCase();

  return (
    <TooltipProvider delayDuration={300}>
      <div className="fixed left-6 top-1/2 -translate-y-1/2 z-50">
        <nav className="bg-card/80 backdrop-blur-xl border border-border rounded-full shadow-2xl p-2">
          <ul className="flex flex-col gap-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <li key={item.path}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        to={item.path}
                        className={cn(
                          'flex items-center justify-center w-10 h-10 rounded-full transition-all duration-300',
                          'hover:bg-primary/10 hover:scale-110',
                          isActive
                            ? 'bg-black text-white shadow-lg hover:bg-black/80 hover:text-white'
                            : 'bg-transparent text-muted-foreground hover:text-primary'
                        )}
                        aria-label={item.label}
                      >
                        <Icon className="w-4 h-4" />
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent
                      side="right"
                      className="bg-black text-white border-black px-2 py-1 text-xs font-medium"
                    >
                      {item.label}
                    </TooltipContent>
                  </Tooltip>
                </li>
              );
            })}

            {/* Profile Picture */}
            <li className="mt-2 border-t border-border pt-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    to="/profile"
                    className="flex items-center justify-center w-10 h-10 transition-all duration-300 hover:scale-110"
                    aria-label="Profile"
                  >
                    <div className="w-8 h-8 rounded-full overflow-hidden">
                      {avatarUrl ? (
                        <img src={avatarUrl} alt="Profile" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white text-xs font-semibold">
                          {initials}
                        </div>
                      )}
                    </div>
                  </Link>
                </TooltipTrigger>
                <TooltipContent
                  side="right"
                  className="bg-black text-white border-black px-2 py-1 text-xs font-medium"
                >
                  Profile
                </TooltipContent>
              </Tooltip>
            </li>

            {/* Logout Button */}
            <li>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => logout()}
                    className="flex items-center justify-center w-10 h-10 rounded-full transition-all duration-300 hover:bg-destructive/10 hover:scale-110 bg-transparent text-muted-foreground hover:text-destructive"
                    aria-label="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent
                  side="right"
                  className="bg-black text-white border-black px-2 py-1 text-xs font-medium"
                >
                  Logout
                </TooltipContent>
              </Tooltip>
            </li>
          </ul>
        </nav>
      </div>
    </TooltipProvider>
  );
};

export default FloatingNavbar;
