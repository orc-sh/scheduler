# Authentication API Examples

This document provides curl examples and code snippets for testing the authentication API.

## Testing with curl

### 1. Get Available OAuth Providers

```bash
curl http://localhost:8000/auth/oauth/providers
```

**Response:**
```json
[
  {
    "name": "google",
    "display_name": "Google"
  },
  {
    "name": "github",
    "display_name": "GitHub"
  }
]
```

### 2. Get OAuth Authorization URL

```bash
curl http://localhost:8000/auth/oauth/google
```

**Response:**
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "provider": "google"
}
```

### 3. Exchange Code for Tokens (after OAuth callback)

```bash
curl -X POST http://localhost:8000/auth/oauth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "authorization_code_from_oauth_provider"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "v1.Mk...",
  "expires_at": 1234567890,
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "user_metadata": {
      "full_name": "John Doe",
      "avatar_url": "https://..."
    }
  }
}
```

### 4. Get Current User Info

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "user_metadata": {
    "full_name": "John Doe",
    "avatar_url": "https://..."
  }
}
```

### 5. Refresh Access Token

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

**Response:**
```json
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "expires_at": 1234567890
}
```

### 6. Logout

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### 7. Access Protected Endpoint (Tasks)

```bash
# Without authentication (will fail with 401)
curl http://localhost:8000/tasks/

# With authentication (success)
curl http://localhost:8000/tasks/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## JavaScript/TypeScript Examples

### Using the API Client (Frontend)

The `api.ts` client automatically handles token attachment and refresh:

```typescript
import api from '@/lib/api';

// Get tasks (token automatically attached)
const response = await api.get('/tasks');
console.log(response.data);

// Create a task
const newTask = await api.post('/tasks', {
  name: 'My Task',
  // ... other task data
});

// Token refresh happens automatically on 401 errors
```

### Using the Auth Context

```typescript
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, loginWithOAuth, logout } = useAuth();

  const handleLogin = async (provider: 'google' | 'github') => {
    try {
      await loginWithOAuth(provider);
      // User will be redirected to OAuth provider
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleLogout = async () => {
    await logout();
    // Tokens cleared, user redirected to login
  };

  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  return (
    <div>
      <p>Welcome, {user?.email}</p>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}
```

## Python Examples (Backend Testing)

### Testing Auth Service

```python
from app.services.auth_service import auth_service

# Get OAuth URL
oauth_url = auth_service.get_oauth_url("google")
print(f"OAuth URL: {oauth_url}")

# Exchange code for session
session_data = await auth_service.exchange_code_for_session("auth_code_here")
print(f"Access Token: {session_data['access_token']}")

# Get user info
user_info = await auth_service.get_user("access_token_here")
print(f"User: {user_info}")
```

### Testing Protected Endpoint

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Without authentication
response = client.get("/tasks/")
assert response.status_code == 401

# With authentication
headers = {"Authorization": "Bearer valid_token_here"}
response = client.get("/tasks/", headers=headers)
assert response.status_code == 200
```

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Authorization header missing"
}
```

### 401 Token Expired

```json
{
  "detail": "Token has expired"
}
```

### 401 Invalid Token

```json
{
  "detail": "Invalid token: ..."
}
```

### 400 Bad Request

```json
{
  "detail": "Provider 'invalid' not supported. Supported providers: google, github"
}
```

### 500 Server Error

```json
{
  "detail": "Failed to initiate OAuth flow: ..."
}
```

## Token Lifecycle

1. **Initial Login:**
   - User clicks OAuth button
   - Gets redirected to provider
   - Returns with authorization code
   - Code exchanged for access_token + refresh_token

2. **API Requests:**
   - access_token sent in Authorization header
   - Backend verifies JWT signature
   - Extracts user info from token

3. **Token Expiration:**
   - Access token expires (typically 1 hour)
   - API returns 401
   - Frontend automatically uses refresh_token
   - Gets new access_token + refresh_token
   - Retries original request

4. **Logout:**
   - Tokens cleared from localStorage
   - Session revoked in Supabase
   - User redirected to login

## Testing Checklist

- [ ] OAuth providers endpoint returns Google and GitHub
- [ ] OAuth URL generation works for both providers
- [ ] OAuth callback successfully exchanges code for tokens
- [ ] Tokens are properly stored in localStorage
- [ ] Protected endpoints reject requests without tokens
- [ ] Protected endpoints accept requests with valid tokens
- [ ] Token refresh works automatically on expiry
- [ ] Logout clears tokens and redirects to login
- [ ] User info endpoint returns correct user data
- [ ] CORS allows requests from frontend origin

## Common Issues & Solutions

**Issue:** "Invalid authorization header format"
**Solution:** Ensure header is formatted as `Authorization: Bearer <token>`

**Issue:** "Token has expired"
**Solution:** Use refresh token endpoint or let auto-refresh handle it

**Issue:** CORS error in browser
**Solution:** Check `FRONTEND_URL` in backend .env and CORS middleware config

**Issue:** "Failed to exchange code for session"
**Solution:** Verify Supabase credentials and OAuth provider configuration

**Issue:** 401 on protected routes
**Solution:** Check token is being sent in Authorization header and is valid

