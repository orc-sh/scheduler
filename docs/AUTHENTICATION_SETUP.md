# Supabase OAuth Authentication Setup Guide

This guide will help you set up OAuth authentication (Google/GitHub) using Supabase with the FastAPI backend and React frontend.

## Prerequisites

- Supabase account (create one at https://supabase.com)
- Google OAuth credentials (for Google login)
- GitHub OAuth App credentials (for GitHub login)

## 1. Supabase Project Setup

### Create a Supabase Project

1. Go to https://supabase.com/dashboard
2. Create a new project
3. Note down your project credentials:
   - Project URL (found in Settings > API)
   - Anon/Public Key (found in Settings > API)
   - JWT Secret (found in Settings > API > JWT Settings)

### Configure OAuth Providers

#### Google OAuth Setup

1. Go to Supabase Dashboard > Authentication > Providers
2. Enable Google provider
3. Create Google OAuth credentials:
   - Visit https://console.cloud.google.com/
   - Create a new project or select existing
   - Navigate to "APIs & Services" > "Credentials"
   - Create OAuth 2.0 Client ID
   - Add authorized redirect URI: `https://your-project.supabase.co/auth/v1/callback`
4. Copy Client ID and Client Secret to Supabase Google provider settings

#### GitHub OAuth Setup

1. Go to Supabase Dashboard > Authentication > Providers
2. Enable GitHub provider
3. Create GitHub OAuth App:
   - Visit https://github.com/settings/developers
   - Click "New OAuth App"
   - Set Authorization callback URL: `https://your-project.supabase.co/auth/v1/callback`
4. Copy Client ID and Client Secret to Supabase GitHub provider settings

## 2. Backend Configuration

### Install Dependencies

```bash
cd services/scheduler
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in `services/scheduler/`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here

# Frontend URL for CORS
FRONTEND_URL=http://localhost:5173

# Your existing database and other configurations
```

### Start the Backend

```bash
cd services/scheduler
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

### Available Endpoints

- `GET /auth/oauth/providers` - List available OAuth providers
- `GET /auth/oauth/{provider}` - Get OAuth authorization URL
- `POST /auth/oauth/callback` - Handle OAuth callback
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `GET /auth/me` - Get current user info
- All `/tasks/*` endpoints now require authentication

## 3. Frontend Configuration

### Environment Variables

Create a `.env` file in `apps/web/`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Start the Frontend

```bash
cd apps/web
npm install  # or pnpm install
npm run dev  # or pnpm dev
```

The app will be available at http://localhost:5173

## 4. Testing the Authentication Flow

1. Navigate to http://localhost:5173
2. You'll be redirected to the login page
3. Click "Continue with Google" or "Continue with GitHub"
4. Authorize the application on the OAuth provider
5. You'll be redirected back to the app and logged in
6. Access the dashboard to see your user information

## 5. How It Works

### Authentication Flow

1. **User clicks OAuth provider button** → Frontend calls `GET /auth/oauth/{provider}`
2. **Backend returns OAuth URL** → User is redirected to Google/GitHub
3. **User authorizes** → OAuth provider redirects to `/auth/callback?code=...`
4. **Frontend extracts code** → Calls `POST /auth/oauth/callback` with code
5. **Backend exchanges code for tokens** → Returns access_token, refresh_token, and user info
6. **Frontend stores tokens** → Sets up axios interceptors for API calls
7. **Protected routes** → All API calls include JWT token in Authorization header
8. **Token refresh** → Automatic refresh when token expires (401 response)

### File Structure

**Backend:**
- `services/scheduler/app/services/auth_service.py` - Supabase OAuth integration
- `services/scheduler/app/middleware/auth_middleware.py` - JWT verification
- `services/scheduler/app/controllers/auth_controller.py` - Auth endpoints
- `services/scheduler/config/environment.py` - Environment configuration

**Frontend:**
- `apps/web/src/lib/api.ts` - Axios client with token interceptors
- `apps/web/src/contexts/AuthContext.tsx` - Authentication state management
- `apps/web/src/pages/LoginPage.tsx` - OAuth login interface
- `apps/web/src/pages/AuthCallbackPage.tsx` - OAuth callback handler
- `apps/web/src/pages/DashboardPage.tsx` - Protected dashboard
- `apps/web/src/components/ProtectedRoute.tsx` - Route protection wrapper

## 6. Security Notes

- JWT tokens are stored in localStorage
- Automatic token refresh on expiry
- All `/tasks` endpoints now require authentication
- CORS is configured to allow frontend origin
- Tokens are automatically attached to API requests
- Failed authentication redirects to login page

## 7. Customization

### Adding More OAuth Providers

1. Enable provider in Supabase Dashboard
2. Update `GET /auth/oauth/providers` endpoint
3. Add provider button in `LoginPage.tsx`

### Adding User Roles

1. Use Supabase custom claims in JWT
2. Check roles in `auth_middleware.py`
3. Implement role-based access control

### Custom User Data

- User metadata is available in `user.user_metadata`
- Extend `UserResponse` model for additional fields
- Store custom data in Supabase user metadata

## 8. Troubleshooting

### "SUPABASE_URL environment variable is not set"
- Ensure `.env` file exists in `services/scheduler/`
- Check that variables are properly set
- Restart the backend server

### OAuth redirect mismatch
- Verify redirect URIs in Google/GitHub OAuth settings
- Must match: `https://your-project.supabase.co/auth/v1/callback`

### CORS errors
- Check `FRONTEND_URL` in backend `.env`
- Verify CORS middleware configuration in `main.py`

### Token refresh fails
- Check `SUPABASE_JWT_SECRET` is correct
- Verify JWT token format in requests
- Check token expiration settings in Supabase

## 9. Production Deployment

1. Update `FRONTEND_URL` to production domain
2. Update `VITE_API_BASE_URL` to production API URL
3. Update OAuth redirect URIs to production URLs
4. Use HTTPS for all endpoints
5. Consider token storage security (HttpOnly cookies vs localStorage)
6. Implement rate limiting for auth endpoints
7. Add logging and monitoring

## Need Help?

- Supabase Documentation: https://supabase.com/docs/guides/auth
- FastAPI Documentation: https://fastapi.tiangolo.com/
- React Router Documentation: https://reactrouter.com/

