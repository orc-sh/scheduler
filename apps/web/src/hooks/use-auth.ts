import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api, { clearTokens } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';

interface User {
  id: string;
  email: string;
  user_metadata: Record<string, any>;
}

interface OAuthUrlResponse {
  url: string;
}

interface OAuthCallbackResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

/**
 * Hook to fetch current user
 */
export const useCurrentUser = () => {
  const setUser = useAuthStore((state) => state.setUser);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = useAuthStore((state) => state.accessToken);

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      try {
        const response = await api.get<User>('/auth/me');
        setUser(response.data);
        return response.data;
      } catch (error) {
        clearTokens();
        setUser(null);
        throw error;
      }
    },
    enabled: isAuthenticated && !!accessToken,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
};

/**
 * Hook to initiate OAuth login
 */
export const useOAuthLogin = () => {
  return useMutation({
    mutationFn: async (provider: string) => {
      const response = await api.get<OAuthUrlResponse>(`/auth/oauth/${provider}`);
      return response.data;
    },
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });
};

/**
 * Hook to handle OAuth callback
 */
export const useOAuthCallback = () => {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (code: string) => {
      const response = await api.post<OAuthCallbackResponse>('/auth/oauth/callback', { code });
      return response.data;
    },
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });
};

/**
 * Hook to logout user
 */
export const useLogout = () => {
  const logout = useAuthStore((state) => state.logout);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await api.post('/auth/logout');
    },
    onSettled: () => {
      logout();
      queryClient.clear();
    },
  });
};
