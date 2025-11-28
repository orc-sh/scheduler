import {
  Home,
  Bell,
  LogOut,
  Moon,
  Sun,
  User,
  Hammer,
  CalendarClock,
  Package,
  Globe,
  TreeDeciduous,
} from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTheme } from 'next-themes';
import { useState, useRef, useEffect } from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useAuthStore } from '@/stores/auth-store';
import { useLogout } from '@/hooks/use-auth';
import { cn } from '@/lib/utils';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';

const FloatingNavbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const { mutate: logout } = useLogout();
  const { theme, setTheme } = useTheme();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  const navItems = [
    {
      icon: Home,
      label: 'Home',
      path: '/',
    },
    {
      icon: Globe,
      label: 'Endpoints',
      path: '/endpoints',
    },
    {
      icon: CalendarClock,
      label: 'Schedules',
      path: '/schedules',
    },
    {
      icon: Bell,
      label: 'Notifications',
      path: '/notifications',
    },
  ];

  const avatarUrl = user?.user_metadata?.avatar_url;
  const userEmail = user?.email || '';
  const initials = userEmail.slice(0, 2).toUpperCase();

  return (
    <TooltipProvider delayDuration={300}>
      <div className="fixed left-2 top-1/2 -translate-y-1/2 z-50">
        <nav className="bg-card/80 h-[calc(100vh-20px)] backdrop-blur-xl border border-border rounded-md shadow-2xl p-2 flex flex-col justify-between">
          <div className="flex flex-col items-center justify-center gap-4">
            <div
              onClick={() => navigate('/')}
              className="w-10 h-10 cursor-pointer rounded-md bg-accent flex items-center justify-center"
            >
              <TreeDeciduous className="text-primary font-black font-poppins" />
            </div>
            <div className="border-t border-border w-full"></div>
            <ul className="flex flex-col gap-1.5 h-calc(100%-40px)">
              {navItems.map((item) => {
                const Icon = item.icon;
                // Match based on URL prefix - for home route, match exactly, otherwise match prefix
                const isActive =
                  item.path === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.path);

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
                              ? 'bg-green-500 text-white shadow-lg hover:bg-green-500/80 hover:text-white'
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
            </ul>
          </div>
          {/* Profile Dropdown */}
          <div className="mt-2 border-t border-border pt-2 h-fit">
            <Popover>
              <PopoverTrigger asChild>
                <button
                  className="flex items-center justify-center w-10 h-10 transition-all duration-300 hover:scale-110 focus:outline-none focus:ring-0"
                  aria-label="Profile Menu"
                  type="button"
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
                </button>
              </PopoverTrigger>
              <PopoverContent
                align="start"
                side="right"
                className="ml-2 w-48 bg-popover border border-border rounded-md shadow-lg z-50 p-1 animate-in fade-in-0 zoom-in-95 slide-in-from-left-2"
              >
                <div className="px-2 py-1.5 text-sm font-semibold text-popover-foreground">
                  My Account
                </div>
                <div className="h-px bg-muted my-1" />

                <button
                  onClick={() => {
                    navigate('/profile');
                  }}
                  className="relative flex w-full cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground text-popover-foreground"
                >
                  <User className="h-4 w-4" />
                  <span>Profile</span>
                </button>

                <button
                  onClick={() => {
                    setTheme(theme === 'dark' ? 'light' : 'dark');
                  }}
                  className="relative flex w-full cursor-pointer select-none items-center justify-between rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground text-popover-foreground"
                >
                  <div className="flex items-center gap-2">
                    {theme === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
                    <span>Dark Mode</span>
                  </div>
                  <div
                    className={cn(
                      'relative inline-flex h-5 w-9 items-center rounded-full transition-colors',
                      theme === 'dark' ? 'bg-primary' : 'bg-input'
                    )}
                  >
                    <span
                      className={cn(
                        'inline-block h-4 w-4 transform rounded-full bg-background shadow-lg transition-transform',
                        theme === 'dark' ? 'translate-x-[1.125rem]' : 'translate-x-0.5'
                      )}
                    />
                  </div>
                </button>

                <div className="h-px bg-muted my-1" />

                <button
                  onClick={() => {
                    logout();
                  }}
                  className="relative flex w-full cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-destructive/10 text-destructive"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </PopoverContent>
            </Popover>
          </div>
        </nav>
      </div>
    </TooltipProvider>
  );
};

export default FloatingNavbar;
