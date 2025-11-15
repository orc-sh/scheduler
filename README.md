# Scheduler Application

A modern scheduler application with Supabase OAuth authentication, FastAPI backend, and React frontend.

## 🚀 Features

- ✅ OAuth authentication (Google & GitHub)
- ✅ JWT token-based API security
- ✅ Automatic token refresh
- ✅ Protected routes and endpoints
- ✅ Modern UI with shadcn/ui components
- ✅ Task scheduling and management

## 📁 Project Structure

```
scheduler/
├── apps/
│   └── web/              # React frontend application
├── services/
│   └── scheduler/        # FastAPI backend service
├── docs/                 # 📚 All documentation
└── docker-compose.yml
```

## 📚 Documentation

All documentation is available in the [`docs/`](./docs/) folder:

- **[Implementation Summary](./docs/IMPLEMENTATION_SUMMARY.md)** - What was built and how it works
- **[Authentication Setup](./docs/AUTHENTICATION_SETUP.md)** - Detailed setup guide
- **[API Examples](./docs/API_AUTHENTICATION_EXAMPLES.md)** - Testing and usage examples

## 🏃 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Supabase account

### 1. Clone and Install

```bash
# Install backend dependencies
cd services/scheduler
pip install -r requirements.txt

# Install frontend dependencies
cd ../../apps/web
npm install
```

### 2. Configure Environment

**Backend** (`services/scheduler/.env`):
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
FRONTEND_URL=http://localhost:5173
```

**Frontend** (`apps/web/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
cd services/scheduler
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd apps/web
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🔐 Authentication

The application uses Supabase for OAuth authentication with Google and GitHub providers. See the [Authentication Setup Guide](./docs/AUTHENTICATION_SETUP.md) for detailed configuration instructions.

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - OAuth authentication
- **SQLAlchemy** - Database ORM
- **Celery** - Task scheduling
- **Redis** - Message broker

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Routing
- **Axios** - HTTP client
- **shadcn/ui** - UI components
- **Tailwind CSS** - Styling

## 📖 API Documentation

### Authentication Endpoints

- `GET /auth/oauth/providers` - List available OAuth providers
- `GET /auth/oauth/{provider}` - Get OAuth authorization URL
- `POST /auth/oauth/callback` - Handle OAuth callback
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Sign out user
- `GET /auth/me` - Get current user info

### Task Endpoints (Protected)

- `GET /tasks/` - List all tasks
- `POST /tasks/` - Create a new task
- `GET /tasks/{task_id}` - Get task details
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task
- `GET /tasks/{task_id}/results` - Get task results

See [API Examples](./docs/API_AUTHENTICATION_EXAMPLES.md) for detailed usage.

## 🧪 Testing

```bash
# Backend tests
cd services/scheduler
pytest

# Frontend tests
cd apps/web
npm test
```

## 📦 Deployment

See the [Authentication Setup Guide](./docs/AUTHENTICATION_SETUP.md#9-production-deployment) for production deployment instructions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

- Check the [documentation](./docs/)
- Review [troubleshooting guide](./docs/AUTHENTICATION_SETUP.md#8-troubleshooting)
- Open an issue on GitHub

## 🙏 Acknowledgments

- [Supabase](https://supabase.com) for authentication
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [shadcn/ui](https://ui.shadcn.com/) for UI components

