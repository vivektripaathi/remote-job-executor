# Remote Job Executor

A production-ready asynchronous remote job execution system built with Django, Celery, and Django Channels. Execute shell commands remotely with real-time log streaming, job prioritization, and comprehensive management capabilities.

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

## Documentation

- **[CLI Documentation](./cli/README.md)** - Complete CLI usage guide with examples and advanced features
- **[Backend Documentation](./backend/README.md)** - Backend architecture, API reference, and development guide

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/vivektripaathi/remote-job-executor
cd remote-job-executor
```

### 2. Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.9+** for CLI usage
- SSH key for remote server access (if executing on remote servers)

### 3. SSH Configuration

Ensure your SSH key is in the project root:

```bash
# Your SSH private key should be at:
./ssh-key.pem

# Update backend/.env.development with your server details:
EC2_HOST=your-server-ip
EC2_USERNAME=your-username
EC2_KEY_PATH=ssh-key.pem
```

### 4. Start with Docker

**Start all services:**

```bash
# Build and start all containers (first time or after changes)
docker-compose build

# Or start without rebuilding (if no changes)
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
# Install CLI dependencies and test
cd cli
python -m venv venv

#  If you're on Mac/Linux:
source venv/bin/activate
# If you're on Windows (PowerShell or CMD):
.\venv\Scripts\activate
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

### Common Issues

**SSH Key Issues:**

- Verify key exists: `ls -la ssh-key.pem`
- Check permissions: `chmod 600 ssh-key.pem`
- Update paths in `.env.development`
