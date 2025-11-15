import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { setTokens, getAccessToken, clearTokens, isAuthenticated } from '@/lib/api';

interface User {
  id: string;
  email: string;
  user_metadata: Record<string, any>;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  loginWithOAuth: (provider: string) => Promise<void>;
  handleOAuthCallback: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  // Fetch current user on mount if token exists
  useEffect(() => {
    const initAuth = async () => {
      if (isAuthenticated()) {
        try {
          await fetchCurrentUser();
        } catch (error) {
          console.error('Failed to fetch user:', error);
          clearTokens();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  /**
   * Fetch current user information from the API
   */
  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
      setAuthenticated(true);
    } catch (error) {
      console.error('Error fetching user:', error);
      setUser(null);
      setAuthenticated(false);
      throw error;
    }
  };

  /**
   * Initiate OAuth login flow
   */
  const loginWithOAuth = async (provider: string) => {
    try {
      const response = await api.get(`/auth/oauth/${provider}`);
      const { url } = response.data;

      // Redirect to OAuth provider
      window.location.href = url;
    } catch (error) {
      console.error('Error initiating OAuth:', error);
      throw error;
    }
  };

  /**
   * Handle OAuth callback and exchange code for tokens
   */
  const handleOAuthCallback = async (code: string) => {
    try {
      setLoading(true);
      const response = await api.post('/auth/oauth/callback', { code });

      const { access_token, refresh_token, user: userData } = response.data;

      // Store tokens
      setTokens(access_token, refresh_token);

      // Set user data
      setUser(userData);
      setAuthenticated(true);
    } catch (error) {
      console.error('Error handling OAuth callback:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Logout user and clear tokens
   */
  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Error logging out:', error);
    } finally {
      clearTokens();
      setUser(null);
      setAuthenticated(false);
    }
  };

  /**
   * Refresh the session (handled automatically by API interceptor)
   */
  const refreshSession = async () => {
    try {
      await fetchCurrentUser();
    } catch (error) {
      console.error('Error refreshing session:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: authenticated,
    loginWithOAuth,
    handleOAuthCallback,
    logout,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Custom hook to use auth context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
