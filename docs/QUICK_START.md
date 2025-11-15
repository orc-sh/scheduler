# Quick Start: Using TanStack Query & Zustand

## 🚀 Getting Started

Your React app now uses TanStack Query and Zustand! Here's everything you need to know to start building.

## 📖 Basic Usage

### 1. Access Authentication State (Zustand)

```typescript
import { useAuthStore } from '@/stores/authStore';

function MyComponent() {
  // Get user
  const user = useAuthStore((state) => state.user);
  
  // Get auth status
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  // Get tokens
  const accessToken = useAuthStore((state) => state.accessToken);
  
  return <div>Welcome {user?.email}</div>;
}
```

### 2. Use Auth Hooks (TanStack Query)

```typescript
import { useCurrentUser, useLogout } from '@/hooks/useAuth';

function Profile() {
  // Fetch current user (cached, auto-refetches)
  const { data: user, isLoading, error } = useCurrentUser();
  
  // Logout mutation
  const { mutate: logout } = useLogout();
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error!</div>;
  
  return (
    <div>
      <p>{user?.email}</p>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}
```

## 🔨 Creating New Features

### Step 1: Create API Functions (Optional but Recommended)

```typescript
// src/lib/todos.ts
import api from './api';

export const todosApi = {
  getAll: async () => {
    const res = await api.get('/todos');
    return res.data;
  },
  
  getById: async (id: string) => {
    const res = await api.get(`/todos/${id}`);
    return res.data;
  },
  
  create: async (data: CreateTodoInput) => {
    const res = await api.post('/todos', data);
    return res.data;
  },
  
  update: async (id: string, data: UpdateTodoInput) => {
    const res = await api.patch(`/todos/${id}`, data);
    return res.data;
  },
  
  delete: async (id: string) => {
    await api.delete(`/todos/${id}`);
  },
};
```

### Step 2: Create TanStack Query Hooks

```typescript
// src/hooks/useTodos.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { todosApi } from '@/lib/todos';

// Fetch all todos
export const useTodos = () => {
  return useQuery({
    queryKey: ['todos'],
    queryFn: todosApi.getAll,
  });
};

// Fetch single todo
export const useTodo = (id: string) => {
  return useQuery({
    queryKey: ['todo', id],
    queryFn: () => todosApi.getById(id),
    enabled: !!id,
  });
};

// Create todo
export const useCreateTodo = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: todosApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

// Update todo
export const useUpdateTodo = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, ...data }: UpdateTodoInput & { id: string }) =>
      todosApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};

// Delete todo
export const useDeleteTodo = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: todosApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
};
```

### Step 3: Use in Components

```typescript
// src/components/TodoList.tsx
import { useTodos, useCreateTodo, useDeleteTodo } from '@/hooks/useTodos';

function TodoList() {
  const { data: todos, isLoading, error } = useTodos();
  const { mutate: createTodo, isPending: isCreating } = useCreateTodo();
  const { mutate: deleteTodo } = useDeleteTodo();
  
  const handleCreate = () => {
    createTodo({ title: 'New Todo' });
  };
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <button onClick={handleCreate} disabled={isCreating}>
        {isCreating ? 'Creating...' : 'Add Todo'}
      </button>
      
      {todos?.map((todo) => (
        <div key={todo.id}>
          <span>{todo.title}</span>
          <button onClick={() => deleteTodo(todo.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
}
```

## 🎨 Creating Zustand Stores

### For App-Wide State (Not Server Data)

```typescript
// src/stores/uiStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ 
        sidebarOpen: !state.sidebarOpen 
      })),
    }),
    { name: 'ui-storage' }
  )
);
```

### Use in Components

```typescript
function Header() {
  const theme = useUIStore((state) => state.theme);
  const setTheme = useUIStore((state) => state.setTheme);
  
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Toggle Theme: {theme}
    </button>
  );
}
```

## 💡 Common Patterns

### Pattern 1: Loading States

```typescript
const { data, isLoading, isFetching, error } = useQuery({...});

// Show spinner on initial load
if (isLoading) return <Spinner />;

// Show error state
if (error) return <ErrorMessage error={error} />;

// Show data with optional background refresh indicator
return (
  <div>
    {isFetching && <RefreshIndicator />}
    <DataDisplay data={data} />
  </div>
);
```

### Pattern 2: Mutations with Feedback

```typescript
const { mutate, isPending, isSuccess, isError, error } = useMutation({...});

return (
  <form onSubmit={(e) => {
    e.preventDefault();
    mutate(formData);
  }}>
    <input {...} />
    <button disabled={isPending}>
      {isPending ? 'Saving...' : 'Save'}
    </button>
    {isSuccess && <div>Saved successfully!</div>}
    {isError && <div>Error: {error.message}</div>}
  </form>
);
```

### Pattern 3: Dependent Queries

```typescript
// First query
const { data: user } = useQuery({
  queryKey: ['user'],
  queryFn: fetchUser,
});

// Second query depends on first
const { data: posts } = useQuery({
  queryKey: ['posts', user?.id],
  queryFn: () => fetchPosts(user.id),
  enabled: !!user?.id, // Only run when user exists
});
```

### Pattern 4: Optimistic Updates

```typescript
const { mutate } = useMutation({
  mutationFn: updateTodo,
  onMutate: async (newData) => {
    // Cancel queries
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    
    // Save previous state
    const previous = queryClient.getQueryData(['todos']);
    
    // Optimistically update UI
    queryClient.setQueryData(['todos'], (old) => {
      return old.map(todo => 
        todo.id === newData.id ? { ...todo, ...newData } : todo
      );
    });
    
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

## 🔧 DevTools

### Open React Query DevTools

1. Start dev server: `npm run dev`
2. Open your app in browser
3. Look for floating React Query logo (bottom-right)
4. Click to open DevTools
5. Inspect queries, mutations, cache

### What You Can Do

- ✅ View all active queries
- ✅ See cached data
- ✅ Check loading states
- ✅ Inspect query keys
- ✅ Manually refetch queries
- ✅ Clear cache
- ✅ View mutations

## 📋 Checklist for New Features

- [ ] Create API functions in `src/lib/`
- [ ] Create TanStack Query hooks in `src/hooks/`
- [ ] Use hooks in components
- [ ] Handle loading states
- [ ] Handle error states
- [ ] Add optimistic updates (optional)
- [ ] Test in DevTools

## ⚠️ Common Mistakes to Avoid

### ❌ Don't Store Server Data in Zustand

```typescript
// BAD - Don't do this
const useStore = create((set) => ({
  todos: [],
  fetchTodos: async () => {
    const data = await api.get('/todos');
    set({ todos: data });
  },
}));
```

```typescript
// GOOD - Use TanStack Query instead
const useTodos = () => {
  return useQuery({
    queryKey: ['todos'],
    queryFn: async () => {
      const res = await api.get('/todos');
      return res.data;
    },
  });
};
```

### ❌ Don't Select Too Much State

```typescript
// BAD - Causes unnecessary re-renders
const store = useAuthStore((state) => state);

// GOOD - Only select what you need
const user = useAuthStore((state) => state.user);
```

### ❌ Don't Forget Query Keys

```typescript
// BAD - Keys should be descriptive and consistent
queryKey: ['data']

// GOOD - Clear and consistent keys
queryKey: ['todos']
queryKey: ['todo', todoId]
queryKey: ['todos', { status: 'active' }]
```

## 🎯 Where to Go Next

1. **Read the Full Guide**: `docs/TANSTACK_ZUSTAND_MIGRATION.md`
2. **Check Examples**: `src/examples/store-and-hooks-example.ts`
3. **Quick Reference**: `docs/QUICK_REFERENCE.md`
4. **Official Docs**:
   - TanStack Query: https://tanstack.com/query/latest
   - Zustand: https://docs.pmnd.rs/zustand

## 🆘 Need Help?

- Check `docs/QUICK_REFERENCE.md` for syntax
- Look at `src/examples/store-and-hooks-example.ts` for patterns
- Use React Query DevTools to debug
- Check the official documentation

---

**Happy coding! 🚀**

