# Remote Job Executor - Backend

A production-ready Django backend for asynchronous remote job execution with clean architecture, dependency injection, and real-time capabilities.

## 🏗️ Architecture Overview

This backend implements **Clean Architecture** with **Domain-Driven Design** principles:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ REST API    │  │ WebSocket   │  │ Celery Tasks        │ │  
│  │ Views       │  │ Consumers   │  │ (Background Jobs)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Use Cases   │  │ Domain      │  │ Business Logic      │ │
│  │ (Services)  │  │ Models      │  │ & Validation        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Repository  │  │ SSH Client  │  │ External Services   │ │
│  │ (Data)      │  │ (Executor)  │  │ & Integrations      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Core Features

### Job Management

- **Create Jobs**: Submit shell commands with priority and timeout settings
- **Status Tracking**: Real-time job status updates (Queued → Running → Success/Failed/Cancelled)
- **Output Capture**: Store stdout and stderr from executed commands
- **Job Cancellation**: Stop running jobs with cleanup
- **Job Listing**: Paginated job lists with filtering

### Real-time Communication

- **WebSocket Streaming**: Live log streaming during job execution
- **Status Updates**: Real-time job status changes via WebSocket
- **Client Notifications**: Immediate feedback on job state changes

### Background Processing

- **Celery Integration**: Asynchronous job execution with Redis broker
- **Priority Queuing**: Low, Medium, High priority job scheduling
- **Retry Logic**: Automatic retry for failed jobs with backoff
- **Task Monitoring**: Comprehensive logging and error handling

### Security & Production Features

- **Environment Configuration**: Separate development/production settings
- **Input Validation**: Pydantic-based request validation
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Database Optimization**: Efficient queries with proper indexing
- **CORS Support**: Configurable cross-origin resource sharing

## 📋 Tech Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|----------|
| **Framework** | Django | 4.2.23 | Web framework |
| **API** | Django REST Framework | 3.16.0 | REST API development |
| **WebSockets** | Django Channels | 4.0.0 | Real-time communication |
| **Task Queue** | Celery | 5.3.6 | Background job processing |
| **Message Broker** | Redis | 6.2.0 | Task queue backend |
| **Database** | PostgreSQL | 12+ | Primary data storage |
| **Validation** | Pydantic | 1.10.2 | Request/response validation |
| **DI Container** | dependency-injector | 4.41.0 | Dependency injection |
| **SSH Client** | Paramiko | 3.5.1 | Remote command execution |
| **Environment** | django-environ | 0.12.0 | Configuration management |

## 🗂️ Project Structure

```text
backend/
├── backend/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py            # Environment-based settings
│   ├── urls.py               # URL routing
│   ├── asgi.py               # ASGI configuration for WebSockets
│   ├── wsgi.py               # WSGI configuration
│   └── celery.py             # Celery configuration
├── jobs/                      # Main application
│   ├── models.py             # Django models (Job)
│   ├── tasks.py              # Celery tasks
│   ├── consumers.py          # WebSocket consumers
│   ├── routing.py            # WebSocket URL routing
│   ├── inject.py             # Dependency injection configuration
│   ├── types.py              # Type definitions
│   ├── exceptions.py         # Custom exceptions
│   ├── domain/               # Domain layer
│   │   ├── domain_models.py  # Pydantic domain models
│   │   └── use_cases/        # Business logic use cases
│   │       ├── create_job_use_case.py
│   │       ├── get_job_use_case.py
│   │       ├── list_jobs_use_case.py
│   │       ├── update_job_use_case.py
│   │       ├── cancel_job_use_case.py
│   │       ├── delete_job_use_case.py
│   │       ├── execute_remote_command_use_case.py
│   │       ├── execute_remote_command_streaming_use_case.py
│   │       └── kill_remote_process_use_case.py
│   ├── data/                 # Data layer
│   │   └── repositories/     # Repository implementations
│   │       └── job_repository.py
│   ├── infrastructure/       # Infrastructure layer
│   │   └── ssh/             # SSH implementations
│   │       ├── ssh_client.py
│   │       └── ssh_executor.py
│   └── presentation/        # Presentation layer
│       ├── views.py         # API views
│       ├── urls.py          # API URL patterns
│       └── types.py         # API request/response types
├── migrations/              # Database migrations
├── requirements.txt         # Python dependencies
├── manage.py               # Django management commands
├── .env.development        # Development environment
├── .env.production         # Production environment template
└── README.md              # This file
```

## ⚙️ Configuration

### Environment Files

> **Note**: The docker-compose configuration uses the main `.env` file. The `.env.development` and `.env.production` files are templates for different deployment scenarios.

**Main Configuration (.env):**

- Used by docker-compose
- Contains active configuration settings

**Development (.env.development):**

```bash
# Core Django Settings
SECRET_KEY=django-insecure-dev-key-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=psql://postgres:postgres@localhost:5432/remote_jobs_dev

# Redis/Celery/Channels  
REDIS_URL=redis://127.0.0.1:6379/0

# Security (Development - Less Strict)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

**Production (.env.production):**

```bash
# Core Django Settings
SECRET_KEY=your-strong-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Database with connection pooling
DATABASE_URL=psql://user:password@db-host:5432/remote_jobs_prod

# Redis with authentication
REDIS_URL=redis://:password@redis-host:6379/0

# Security (Production - Strict)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Django Settings Features

- **Environment-based configuration** using django-environ
- **Database connection pooling** for production
- **Security headers** and HTTPS enforcement
- **CORS configuration** for frontend integration
- **Logging configuration** with structured output
- **Celery integration** with Redis backend
- **Django Channels** for WebSocket support

## 🔌 API Endpoints

### Job Management Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| **POST** | `/jobs/` | Create job | `JobCreateRequest` | `JobResponse` |
| **GET** | `/jobs/list/` | List jobs | Query params | `JobListResponse` |
| **GET** | `/jobs/{id}/` | Get job details | - | `JobResponse` |
| **PUT** | `/jobs/{id}/` | Update job | `JobUpdateRequest` | `JobResponse` |
| **DELETE** | `/jobs/{id}/` | Delete job | - | `204 No Content` |
| **POST** | `/jobs/{id}/cancel/` | Cancel job | - | `JobResponse` |

### Request/Response Types

**JobCreateRequest:**

```json
{
    "command": "string",
    "priority": "Low|Medium|High",
    "timeout": 60,
    "streaming": false
}
```

**JobResponse:**

```json
{
    "id": "uuid",
    "command": "string",
    "priority": "Medium",
    "status": "Queued",
    "timeout": 60,
    "stdout": "string|null",
    "stderr": "string|null",
    "created_at": "2025-01-30T12:00:00Z",
    "started_at": "2025-01-30T12:00:01Z|null",
    "completed_at": "2025-01-30T12:00:05Z|null"
}
```

**JobListResponse:**

```json
{
    "jobs": [JobResponse],
    "total_count": 42
}
```

### Query Parameters (List Jobs)

- `limit`: Number of jobs to return (default: 10, max: 100)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status (Queued|Running|Success|Failed|Cancelled)
- `priority`: Filter by priority (Low|Medium|High)
- `ordering`: Sort field (-created_at, -priority, etc.)

## 🔄 WebSocket API

### Job Log Streaming

**Connect:** `ws://localhost:8000/ws/jobs/{job_id}/`

**Message Format:**

```json
{
    "log": "command output line",
    "status": "Running|Success|Failed|Cancelled",
    "timestamp": "2025-01-30T12:00:00Z"
}
```

**Connection Lifecycle:**

1. Client connects with job ID
2. Server joins client to job-specific group
3. Server streams real-time logs as they're generated
4. Connection closes when job completes or client disconnects

## 🔧 Celery Tasks

### Background Job Execution

**Task: `run_job`**

- Executes shell commands via SSH
- Updates job status in real-time
- Captures stdout and stderr
- Handles timeouts and errors
- Supports job cancellation

**Task: `run_streaming_job`**

- Real-time log streaming via WebSocket
- Line-by-line output broadcasting
- Status update notifications
- Cleanup on completion/cancellation

### Task Configuration

- **Max retries**: 3 attempts
- **Retry backoff**: 30 seconds
- **Task routing**: Priority-based queues
- **Result backend**: Redis for result storage
- **Task monitoring**: Built-in Celery monitoring

## 🧪 Development Setup

### 1. Environment Configuration

First, set up your environment file:

```bash
# Copy the development template to create your active .env file
cp .env.development .env

# Edit the .env file with your actual configuration
# Required updates:
# - EC2_HOST=your-server-ip              # IP address of your remote server
# - EC2_USERNAME=your-username           # SSH username (e.g., ubuntu, ec2-user)  
# - SECRET_KEY=your-secret-key-here      # Generate a strong Django secret key
# Note: EC2_KEY_PATH=/app/ssh-key.pem is already correctly set for Docker

# Example:
# EC2_HOST=192.168.1.100
# EC2_USERNAME=ubuntu
```

### 2. Docker Setup (Recommended)

```bash
# From project root
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f server
docker-compose logs -f celery_worker
```

**Services started:**

- **API Server**: `http://localhost:8000` (Daphne ASGI server)
- **PostgreSQL**: `localhost:5433`
- **Redis**: `localhost:6380`
- **Celery Worker**: Background processing
- **WebSocket**: `ws://localhost:8000/ws/jobs/{job_id}/`

### 3. SSH Configuration

For remote job execution, ensure your SSH key is configured:

```bash
# Ensure SSH key exists in project root
ls -la ssh-key.pem

# Set correct permissions
chmod 600 ssh-key.pem

# Verify .env file has correct SSH settings (from step 1)
grep -E "EC2_HOST|EC2_USERNAME|EC2_KEY_PATH" .env
```
