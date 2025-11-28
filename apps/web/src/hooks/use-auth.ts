import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api, { clearTokens } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';
import { toast } from '@/hooks/use-toast';
import type { User, OAuthUrlResponse, OAuthCallbackResponse } from '@/types';

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
        const response = await api.get<User>('/api/auth/me');
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
      const response = await api.get<OAuthUrlResponse>(`/api/oauth/${provider}`);
      return response.data;
    },
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });
};

/**
 * Hook to login with email and password
 */
export const useEmailPasswordLogin = () => {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: { email: string; password: string }) => {
      const response = await api.post<OAuthCallbackResponse>('/api/auth/login', params);
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
 * Hook to sign up with email and password
 */
export const useEmailPasswordSignup = () => {
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      firstname: string;
      lastname: string;
      email: string;
      password: string;
    }) => {
      const response = await api.post<OAuthCallbackResponse>('/api/auth/register', params);
      return response.data;
    },
    onSuccess: (data) => {
      // Only set tokens if they're not empty (email confirmation might be required)
      if (data.access_token && data.refresh_token) {
        setTokens(data.access_token, data.refresh_token);
        setUser(data.user);
        queryClient.invalidateQueries({ queryKey: ['currentUser'] });
        // Redirect to dashboard if tokens are valid
        window.location.href = '/';
      } else {
        // Email confirmation required - clear auth and show success message on same page
        clearAuth();
        // Success state will be shown in the component
      }
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
      const response = await api.post<OAuthCallbackResponse>('/api/oauth/callback', { code });
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
      await api.post('/api/auth/logout');
    },
    onSettled: () => {
      logout();
      queryClient.clear();
    },
  });
};

/**
 * Hook to send forgot password email
 */
export const useForgotPassword = () => {
  return useMutation({
    mutationFn: async (params: { email: string }) => {
      const response = await api.post<{ message: string }>('/api/auth/forgot-password', params);
      return response.data;
    },
  });
};

/**
 * Hook to reset password
 */
export const useResetPassword = () => {
  return useMutation({
    mutationFn: async (params: { password: string; token: string }) => {
      const response = await api.post<{ message: string }>('/api/auth/reset-password', params);
      return response.data;
    },
  });
};
