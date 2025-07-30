# Remote Job Executor

A production-ready asynchronous remote job execution system built with Django, Celery, and Django Channels. Execute shell commands remotely with real-time log streaming, job prioritization, and comprehensive management capabilities.

## 🐳 Quick Docker Setup

```bash
# Clone and start
git clone <repository-url>
cd remote-job-executor
docker-compose up -d

# Install CLI dependencies and test
cd cli && pip3 install -r requirements.txt
python3 main.py submit "date" --stream
```

**→ WebSocket streaming ready in under 2 minutes!**

## 🚀 Features

- **Asynchronous Job Execution**: Execute shell commands remotely using Celery for background processing
- **Real-time Log Streaming**: WebSocket-based live log streaming with Django Channels
- **Job Management**: Create, view, cancel, and monitor job status and output
- **Priority Scheduling**: Low, Medium, and High priority job queuing
- **Clean Architecture**: Domain-driven design with dependency injection
- **Production Ready**: Environment-based configuration, security settings, and monitoring
- **CLI Interface**: Full-featured command-line interface for job management

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────────┐
│   CLI Client    │    │  Django Backend │    │     Celery Worker    │
│                 │    │                 │    │                      │
│ • Job Submit    │───▶│ • REST API      │───▶│ • SSH Execution      │
│ • Status Check  │    │ • WebSocket     │    │ • Process Management │
│ • Log Stream    │◀───│ • Job Models    │◀───│ • Result Store       │
│ • Cancel Jobs   │    │                 │    │                      │
└─────────────────┘    └─────────────────┘    └──────────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌─────────────┐         ┌─────────────┐
                       │ PostgreSQL  │         │    Redis    │
                       │             │         │             │
                       │ • Job Data  │         │ • Messages  │
                       │ • Metadata  │         │ • Results   │
                       └─────────────┘         └─────────────┘
```

### Technology Stack

- **Backend**: Django 4.2.23 + Django REST Framework
- **Task Queue**: Celery 5.3.6 with Redis broker
- **WebSockets**: Django Channels for real-time communication
- **Database**: PostgreSQL with environment-based configuration
- **Architecture**: Clean Architecture with Domain-Driven Design
- **Dependency Injection**: Using dependency-injector library
- **CLI**: Click-based command-line interface

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd remote-job-executor
```

### 2. Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.9+** for CLI usage
- SSH key for remote server access (if executing on remote servers)

### 3. Configure SSH Key (Optional)

If you want to execute jobs on remote servers, ensure your SSH key is in the project root:

```bash
# Your SSH private key should be at:
./ssh-key.pem

# Update backend/.env.development with your server details:
EC2_HOST=your-server-ip
EC2_USERNAME=your-username
EC2_KEY_PATH=/Users/vivektripathi/Developer/remote-job-executor/ssh-key.pem
```

### 4. Start with Docker

**Start all services:**

```bash
# Build and start all containers
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f server
```

**Services started:**

- **API Server**: `http://localhost:8000` (Daphne ASGI server with WebSocket support)
- **PostgreSQL**: `localhost:5433`
- **Redis**: `localhost:6380`  
- **Celery Worker**: Background job processing
- **WebSocket**: `ws://localhost:8000/ws/jobs/<job-id>/`

### 5. Install CLI Dependencies

```bash
cd cli
pip3 install -r requirements.txt
```

### 6. Test the System

**Submit a job with real-time streaming:**

```bash
cd cli
python3 main.py submit "date" --stream
```

**View job details:**

```bash
python3 main.py view <job-id>
```

**Stop services:**

```bash
docker-compose down
```

## 📁 Project Structure

```text

remote-job-executor/
├── README.md                   # This file
├── backend/                    # Django backend application
│   ├── README.md              # Backend-specific documentation
│   ├── backend/               # Django project settings
│   ├── jobs/                  # Main application
│   │   ├── domain/            # Domain layer (business logic)
│   │   ├── data/              # Data layer (repositories)
│   │   ├── infrastructure/    # Infrastructure layer (SSH, external services)
│   │   ├── presentation/      # Presentation layer (API views)
│   │   ├── models.py          # Django models
│   │   ├── tasks.py           # Celery tasks
│   │   └── consumers.py       # WebSocket consumers
│   ├── requirements.txt       # Python dependencies
│   └── manage.py              # Django management script
├── cli/                       # Command-line interface
│   ├── README.md              # CLI-specific documentation
│   ├── main.py                # CLI entry point
│   ├── utils.py               # Utility functions
│   ├── .env.example           # CLI environment template
│   └── .env                   # CLI environment configuration
└── venv/                      # Virtual environment (gitignored)
```

## 🔧 Configuration

### Backend Configuration (.env)

```bash
# Core Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
DATABASE_URL=psql://user:password@localhost:5432/remote_jobs

# Redis/Celery
REDIS_URL=redis://127.0.0.1:6379/0

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### CLI Configuration (.env)

```bash
# API Endpoints
REMOTE_JOB_API_URL=http://localhost:8000/jobs
REMOTE_JOB_WS_URL=ws://localhost:8000/ws/jobs
```

## 🎯 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs/` | Create new job |
| GET | `/jobs/list/` | List jobs with filtering |
| GET | `/jobs/{id}/` | Get job details |
| POST | `/jobs/{id}/cancel/` | Cancel job |
| WS | `/ws/jobs/{id}/` | Real-time log streaming |

## 🖥️ CLI Usage

> **Prerequisites**: Ensure Docker containers are running (`docker-compose up -d`) and CLI dependencies are installed (`pip3 install -r cli/requirements.txt`)

### Basic Commands

```bash
cd cli

# Submit a job with real-time streaming
python3 main.py submit "date" --stream

# Submit a job with priority
python3 main.py submit "ls -la" --priority High

# View job details
python3 main.py view <job-id>

# Stream job logs in real-time
python3 main.py stream <job-id>

# Cancel a running job
python3 main.py cancel <job-id> --force
```

### Advanced Usage

```bash
cd cli

# Submit with streaming and custom timeout
python3 main.py submit "find /home -name '*.log'" --stream --timeout 120

# Submit and wait for completion
python3 main.py submit "backup-script.sh" --wait --timeout 3600

# Follow job status updates
python3 main.py view <job-id> --follow

# Test with Docker environment
python3 main.py submit "echo 'Docker WebSocket test'" --stream
```

### Docker Integration

The CLI connects to the containerized backend:

- **API Endpoint**: `http://localhost:8000/jobs`
- **WebSocket Endpoint**: `ws://localhost:8000/ws/jobs/<job-id>/`
- **Backend logs**: `docker-compose logs -f server`
- **Worker logs**: `docker-compose logs -f celery_worker`

## 🔒 Security Features

- Environment-based secret management
- CSRF protection and secure cookies
- SSL/TLS ready configuration
- Input validation and sanitization
- Job isolation and timeout protection

## 📊 Monitoring & Observability

- Structured logging with configurable levels
- Job execution metrics and timing
- Real-time status updates via WebSockets
- Celery task monitoring
- Database query optimization

## 🚀 Production Deployment

1. **Environment Setup**: Use `.env.production` template
2. **Database**: Configure PostgreSQL with connection pooling
3. **Redis**: Set up Redis with persistence if needed
4. **Web Server**: Use Gunicorn + Nginx for production serving
5. **Process Management**: Use systemd or supervisor for service management
6. **Monitoring**: Integrate with your monitoring stack (Prometheus, etc.)

## 🧪 Testing

### Docker Testing

```bash
# Start services
docker-compose up -d

# Test WebSocket streaming
cd cli
python3 main.py submit "date" --stream

# Test job management
python3 main.py submit "echo 'Docker test'" --wait

# Check container logs
docker-compose logs -f server
docker-compose logs -f celery_worker
```

### Backend Unit Tests

```bash
# Run tests in container
docker-compose exec server python manage.py test

# Or run locally
cd backend
python manage.py test
```

## 🔧 Troubleshooting

### Docker Issues

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs -f

# Restart services
docker-compose restart

# Clean rebuild
docker-compose down
docker-compose up -d --build
```

### Common Issues

**WebSocket Connection Failed:**

- Ensure Daphne server is running (not runserver)
- Check `docker-compose logs -f server`
- Verify WebSocket URL: `ws://localhost:8000/ws/jobs/<job-id>/`

**SSH Key Issues:**

- Verify key exists: `ls -la ssh-key.pem`
- Check permissions: `chmod 600 ssh-key.pem`
- Update paths in `.env.development`

**Port Conflicts:**

- API (8000), PostgreSQL (5433), Redis (6380)
- Change ports in `docker-compose.yml` if needed

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/backend/README.md` and `/cli/README.md` for detailed component documentation
- **Issues**: Report bugs or request features via GitHub Issues
- **Architecture**: Built with Clean Architecture principles for maintainability and extensibility

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
  - Asynchronous job execution
  - Real-time log streaming
  - CLI interface
  - Clean architecture implementation
  - Production-ready configuration
