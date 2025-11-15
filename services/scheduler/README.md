# Orc - A Lightweight Webhook Scheduler

A lightweight tool to schedule and automate webhooks using cron expressions.

## Local Development Setup

### Prerequisites

- Python 3.10 or higher
- MySQL database
- Redis server (running on localhost:6379)
- Git
- Bash shell (Git Bash on Windows)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rubanthilak/orc.git
   cd orc
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   # On Windows
   .\env\Scripts\activate
   # On Unix or MacOS
   source env/bin/activate
   ```

3. Install dependencies using the install script:
   ```bash
   # This will install both main and development dependencies
   ./bin/install.sh
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following variables (adjust values as needed):
   ```
   # Database
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/orc
   
   # Redis
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

### Running the Application

The project includes several convenience scripts in the `bin` directory to help you run different components of the application.

1. Start the Redis server (required for Celery)

2. Initialize the database:
   ```bash
   alembic upgrade head
   ```

3. Start the application components (each in a separate terminal):

   ```bash
   # Start the FastAPI application (http://localhost:8000)
   ./bin/run.sh

   # Start Celery worker
   ./bin/celery.sh

   # Start Celery beat scheduler (uses SQLAlchemy scheduler)
   ./bin/beat.sh

   # Start Flower monitoring (http://localhost:4000)
   ./bin/flower.sh
   ```

The application will be available at `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

### Development Tools

- **Celery Flower**: Monitor Celery tasks at `http://localhost:4000`
  - Provides task monitoring and management interface
  - Uses Redis as broker and API backend

- **Code Formatting**:
  ```bash
  ./bin/format.sh
  ```
  This script runs a sequence of formatting tools:
  - `isort`: Sorts and formats imports
  - `autoflake`: Removes unused imports and variables
  - `black`: Formats Python code according to PEP 8

### Script Reference

The `bin` directory contains several useful scripts:
- `install.sh`: Installs all dependencies (main and development)
- `run.sh`: Starts the FastAPI application with auto-reload
- `celery.sh`: Starts the Celery worker with event monitoring
- `beat.sh`: Starts the Celery beat scheduler using SQLAlchemy backend
- `flower.sh`: Starts the Flower monitoring tool on port 4000
- `format.sh`: Runs the code formatting pipeline

Note: On Windows, these scripts should be run using Git Bash or a similar Bash shell.