# TanStack Query & Zustand Integration Guide

This document describes the integration of TanStack Query (React Query) and Zustand for state management in the React application.

## Overview

The application has been refactored to use:
- **Zustand**: For global state management (auth state)
- **TanStack Query**: For server state management (API calls, caching, mutations)

## Architecture

### Zustand Store

#### Auth Store (`src/stores/authStore.ts`)

The auth store manages authentication state globally using Zustand with persistence:

```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  logout: () => void;
}
```

**Features:**
- Persists tokens to localStorage automatically
- Provides reactive state updates across components
- Lightweight and performant
- Type-safe with TypeScript

**Usage:**
```typescript
import { useAuthStore } from '@/stores/authStore';

function MyComponent() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const setTokens = useAuthStore((state) => state.setTokens);
  
  // Use the state...
}
```

### TanStack Query Hooks

#### Query Provider (`src/providers/QueryProvider.tsx`)

Sets up the TanStack Query client with default configurations:

```typescript
defaultOptions: {
  queries: {
    staleTime: 60 * 1000, // 1 minute
    refetchOnWindowFocus: false,
    retry: 1,
  },
  mutations: {
    retry: 1,
  },
}
```

**Features:**
- Automatic caching and deduplication
- Background refetching
- Request retries
- DevTools for debugging (in development)

#### Auth Hooks (`src/hooks/useAuth.ts`)

Custom hooks for authentication operations:

##### 1. `useCurrentUser()`

Fetches and caches the current user data:

```typescript
const { data: user, isLoading, error } = useCurrentUser();
```

**Features:**
- Only runs when user is authenticated
- Caches for 5 minutes
- Automatically updates Zustand store
- Handles errors gracefully

##### 2. `useOAuthLogin()`

Initiates OAuth login flow:

```typescript
const { mutate: loginWithOAuth, isPending, variables } = useOAuthLogin();

loginWithOAuth('google');
// or
loginWithOAuth('github');
```

**Features:**
- Mutation-based for side effects
- Tracks loading state per provider
- Redirects to OAuth provider automatically

##### 3. `useOAuthCallback()`

Handles OAuth callback and token exchange:

```typescript
const { mutate: handleOAuthCallback } = useOAuthCallback();

handleOAuthCallback(code, {
  onSuccess: () => navigate('/dashboard'),
  onError: (err) => setError(err.message),
});
```

**Features:**
- Stores tokens in Zustand store
- Updates user state
- Invalidates cached queries
- Provides success/error callbacks

##### 4. `useLogout()`

Logs out the user:

```typescript
const { mutate: logout } = useLogout();

logout();
```

**Features:**
- Clears all auth state
- Clears all cached queries
- Calls backend logout endpoint

## Migration from AuthContext

### Before (AuthContext)

```typescript
import { useAuth } from '@/contexts/AuthContext';

function Component() {
  const { user, loading, isAuthenticated, logout } = useAuth();
  
  const handleLogout = async () => {
    await logout();
  };
  
  return <div>{user?.email}</div>;
}
```

### After (Zustand + TanStack Query)

```typescript
import { useAuthStore } from '@/stores/authStore';
import { useCurrentUser, useLogout } from '@/hooks/useAuth';

function Component() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { isLoading } = useCurrentUser();
  const { mutate: logout } = useLogout();
  
  const handleLogout = () => {
    logout();
  };
  
  return <div>{user?.email}</div>;
}
```

## Benefits

### 1. **Better Performance**

- Zustand is lightweight and only re-renders components that use specific state slices
- TanStack Query automatically caches and deduplicates requests
- No unnecessary re-renders from context updates

### 2. **Better Developer Experience**

- DevTools for inspecting queries and mutations
- Clear separation between client state (Zustand) and server state (TanStack Query)
- Type-safe hooks and state
- Better error handling

### 3. **More Features**

- Automatic background refetching
- Request deduplication
- Optimistic updates (can be added easily)
- Pagination and infinite queries support
- Retry logic built-in

### 4. **Easier Testing**

- Zustand stores can be tested independently
- TanStack Query hooks can be mocked easily
- No complex context setup needed

## Updated Components

### Components Updated

1. **App.tsx**: Added `QueryProvider`, removed `AuthProvider`
2. **LoginPage.tsx**: Uses `useOAuthLogin` hook
3. **DashboardPage.tsx**: Uses `useCurrentUser`, `useLogout`, and `useAuthStore`
4. **AuthCallbackPage.tsx**: Uses `useOAuthCallback` hook
5. **ProtectedRoute.tsx**: Uses `useAuthStore` and `useCurrentUser`

### API Integration (`src/lib/api.ts`)

Updated to use Zustand store for token management:

```typescript
// Get tokens from Zustand
export const getAccessToken = (): string | null => {
  return useAuthStore.getState().accessToken;
};

// Store tokens in Zustand
export const setTokens = (accessToken: string, refreshToken: string) => {
  useAuthStore.getState().setTokens(accessToken, refreshToken);
};
```

## Best Practices

### 1. State Management

- Use **Zustand** for global client state (auth, UI state, etc.)
- Use **TanStack Query** for server state (API data, caching)
- Keep state as local as possible

### 2. Query Keys

Always use consistent query keys for caching:

```typescript
// Good
queryKey: ['currentUser']
queryKey: ['todos', { status: 'active' }]

// Bad (not consistent)
queryKey: ['user']
queryKey: ['User']
```

### 3. Mutations

Use TanStack Query mutations for side effects:

```typescript
const mutation = useMutation({
  mutationFn: (data) => api.post('/endpoint', data),
  onSuccess: () => {
    // Invalidate and refetch queries
    queryClient.invalidateQueries({ queryKey: ['data'] });
  },
});
```

### 4. Loading States

Leverage built-in loading states:

```typescript
const { data, isLoading, isFetching, error } = useQuery({...});

if (isLoading) return <Spinner />;
if (error) return <Error error={error} />;
return <Data data={data} />;
```

## Next Steps

### Recommended Enhancements

1. **Add more Zustand stores** for other global state:
   - UI state (theme, sidebar open/closed)
   - User preferences
   - Notifications

2. **Create more TanStack Query hooks** for API operations:
   - CRUD operations for todos/tasks
   - User profile updates
   - File uploads

3. **Add optimistic updates** for better UX:
   ```typescript
   useMutation({
     mutationFn: updateTodo,
     onMutate: async (newTodo) => {
       // Optimistically update the UI
       await queryClient.cancelQueries({ queryKey: ['todos'] });
       const previousTodos = queryClient.getQueryData(['todos']);
       queryClient.setQueryData(['todos'], (old) => [...old, newTodo]);
       return { previousTodos };
     },
     onError: (err, newTodo, context) => {
       // Rollback on error
       queryClient.setQueryData(['todos'], context.previousTodos);
     },
   });
   ```

4. **Add pagination/infinite queries** for lists:
   ```typescript
   const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
     queryKey: ['todos'],
     queryFn: ({ pageParam = 1 }) => fetchTodos(pageParam),
     getNextPageParam: (lastPage) => lastPage.nextPage,
   });
   ```

## Resources

- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Zustand Docs](https://docs.pmnd.rs/zustand/getting-started/introduction)
- [TanStack Query DevTools](https://tanstack.com/query/latest/docs/framework/react/devtools)

