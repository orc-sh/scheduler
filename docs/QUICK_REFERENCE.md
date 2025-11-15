# TanStack Query & Zustand Quick Reference

## Zustand Store Usage

### Creating a Store

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface MyState {
  count: number;
  increase: () => void;
}

export const useMyStore = create<MyState>()(
  persist(
    (set) => ({
      count: 0,
      increase: () => set((state) => ({ count: state.count + 1 })),
    }),
    { name: 'my-storage' }
  )
);
```

### Using a Store

```typescript
// Select specific state
const count = useMyStore((state) => state.count);

// Select action
const increase = useMyStore((state) => state.increase);

// Select multiple values
const { count, increase } = useMyStore((state) => ({
  count: state.count,
  increase: state.increase,
}));

// Access outside React components
const count = useMyStore.getState().count;
useMyStore.getState().increase();
```

## TanStack Query Hooks

### Query (GET requests)

```typescript
import { useQuery } from '@tanstack/react-query';

const { 
  data,           // The data returned from the query
  isLoading,      // Initial loading state
  isFetching,     // Background fetching state
  error,          // Error object if query failed
  refetch,        // Function to manually refetch
} = useQuery({
  queryKey: ['key'],                    // Unique key for caching
  queryFn: async () => {                // Function to fetch data
    const response = await api.get('/endpoint');
    return response.data;
  },
  enabled: true,                        // Enable/disable query
  staleTime: 60 * 1000,                // Data fresh for 1 minute
  retry: 1,                             // Retry failed requests once
});
```

### Mutation (POST, PUT, PATCH, DELETE)

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();

const { 
  mutate,         // Function to trigger mutation
  isPending,      // Loading state
  error,          // Error object
  data,           // Response data
} = useMutation({
  mutationFn: async (input) => {
    const response = await api.post('/endpoint', input);
    return response.data;
  },
  onSuccess: (data) => {
    // Invalidate and refetch queries
    queryClient.invalidateQueries({ queryKey: ['key'] });
  },
  onError: (error) => {
    console.error('Mutation failed:', error);
  },
});

// Trigger mutation
mutate({ name: 'value' });

// With callbacks
mutate({ name: 'value' }, {
  onSuccess: (data) => console.log('Success:', data),
  onError: (err) => console.error('Error:', err),
});
```

## Common Patterns

### Authentication State

```typescript
// Get auth state
const user = useAuthStore((state) => state.user);
const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

// Login
const { mutate: login } = useOAuthLogin();
login('google');

// Logout
const { mutate: logout } = useLogout();
logout();
```

### Fetching Data

```typescript
// Simple fetch
const { data: users, isLoading } = useQuery({
  queryKey: ['users'],
  queryFn: async () => {
    const res = await api.get('/users');
    return res.data;
  },
});

// With parameters
const { data: user } = useQuery({
  queryKey: ['user', userId],
  queryFn: async () => {
    const res = await api.get(`/users/${userId}`);
    return res.data;
  },
  enabled: !!userId, // Only fetch when userId exists
});
```

### Creating/Updating Data

```typescript
const queryClient = useQueryClient();

const { mutate: createUser } = useMutation({
  mutationFn: async (newUser) => {
    const res = await api.post('/users', newUser);
    return res.data;
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['users'] });
  },
});

// Usage
createUser({ name: 'John', email: 'john@example.com' });
```

### Loading States

```typescript
const { data, isLoading, isFetching } = useQuery({...});

if (isLoading) {
  return <Spinner />; // Initial load
}

return (
  <div>
    {isFetching && <RefreshIndicator />} {/* Background refetch */}
    <DataDisplay data={data} />
  </div>
);
```

### Error Handling

```typescript
const { data, error, isError } = useQuery({...});

if (isError) {
  return <ErrorMessage error={error} />;
}
```

### Optimistic Updates

```typescript
const { mutate } = useMutation({
  mutationFn: updateTodo,
  onMutate: async (newData) => {
    // Cancel outgoing queries
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    
    // Snapshot previous value
    const previous = queryClient.getQueryData(['todos']);
    
    // Optimistically update
    queryClient.setQueryData(['todos'], (old) => [...old, newData]);
    
    return { previous };
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(['todos'], context.previous);
  },
  onSettled: () => {
    // Refetch after mutation
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

### Dependent Queries

```typescript
// First query
const { data: user } = useQuery({
  queryKey: ['user', userId],
  queryFn: fetchUser,
});

// Second query depends on first
const { data: posts } = useQuery({
  queryKey: ['posts', user?.id],
  queryFn: () => fetchUserPosts(user.id),
  enabled: !!user?.id, // Only run when user is available
});
```

## Query Keys Best Practices

```typescript
// ✅ Good
['users']                          // All users
['user', userId]                   // Specific user
['users', { status: 'active' }]    // Filtered users
['posts', { userId, limit: 10 }]   // Parameterized posts

// ❌ Bad
['users', status]                  // Inconsistent structure
['User']                           // Inconsistent casing
[userId]                           // Not descriptive
```

## Cache Manipulation

```typescript
const queryClient = useQueryClient();

// Invalidate (trigger refetch)
queryClient.invalidateQueries({ queryKey: ['users'] });

// Update cache directly
queryClient.setQueryData(['user', '123'], newUserData);

// Get cached data
const users = queryClient.getQueryData(['users']);

// Remove from cache
queryClient.removeQueries({ queryKey: ['user', '123'] });

// Clear all cache
queryClient.clear();
```

## Configuration

### Query Defaults

```typescript
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,           // 1 minute
      cacheTime: 5 * 60 * 1000,       // 5 minutes
      refetchOnWindowFocus: false,     // Don't refetch on focus
      retry: 1,                        // Retry once
    },
  },
});
```

## DevTools

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

Open DevTools: Press the React Query icon in your browser

## Common Issues

### 1. Stale Data

```typescript
// Problem: Data doesn't update
// Solution: Reduce staleTime or invalidate queries
queryClient.invalidateQueries({ queryKey: ['users'] });
```

### 2. Too Many Requests

```typescript
// Problem: Too many API calls
// Solution: Increase staleTime
useQuery({
  queryKey: ['users'],
  queryFn: fetchUsers,
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

### 3. Race Conditions

```typescript
// Problem: Outdated data shown
// Solution: Use cancelQueries in onMutate
onMutate: async () => {
  await queryClient.cancelQueries({ queryKey: ['todos'] });
  // ...
}
```

## TypeScript Tips

```typescript
// Type query data
const { data } = useQuery<User[]>({...});

// Type mutation variables
const { mutate } = useMutation<Response, Error, Variables>({...});

// Type store state
interface MyState {
  count: number;
}
const useMyStore = create<MyState>()((set) => ({...}));
```

