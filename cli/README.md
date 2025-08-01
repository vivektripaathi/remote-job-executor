# Remote Job Executor - CLI

A powerful command-line interface for managing remote job execution with real-time streaming, job monitoring, and comprehensive management capabilities.

## 🚀 Features

- **Job Submission**: Submit shell commands with priority and timeout settings
- **Real-time Streaming**: Live log streaming during job execution
- **Job Monitoring**: View detailed job status, output, and metadata  
- **Job Control**: Cancel running jobs with confirmation
- **Status Following**: Follow job progress in real-time
- **Output Formats**: Table and JSON display options
- **Environment Configuration**: Flexible API endpoint configuration

## 📋 Prerequisites

- Python 3.9+
- Access to Remote Job Executor backend API
- Network connectivity to backend server

## 🛠️ Installation

### 1. Start Backend Services

First, ensure the Docker backend is running:

```bash
# From project root
cd ..
docker-compose up -d --build

# Verify services are running
docker-compose ps
```

### 2. Install CLI Dependencies

```bash
# From CLI directory
cd cli
python3 -m vevn venv
source venv/bin/activate
pip3 install -r requirements.txt
```

**Dependencies installed:**

- `click==8.1.8` - Command-line interface framework
- `requests==2.32.4` - HTTP client for API calls
- `websockets==15.0.1` - WebSocket client for real-time streaming

### 3. Configure Environment

The CLI uses default endpoints that work with Docker setup:

```bash
# Copy environment template (optional)
cp .env.example .env

# Default configuration works with Docker:
REMOTE_JOB_API_URL=http://localhost:8000/jobs
REMOTE_JOB_WS_URL=ws://localhost:8000/ws/jobs
```

### 4. Verify Connection

```bash
# Test basic job submission
python3 main.py submit "date" --stream

# Test API connectivity
python3 main.py submit "echo 'Hello Remote Jobs!'" --wait
```

## 🧪 Testing

The CLI includes two tests designed to validate race conditions and ensure system reliability. These tests simulate common concurrency issues in real-world scenarios:

### Example 1 - Consider an ATM Withdrawal

Imagine Ram and his friend Sham both have access to the same bank account. They attempt to withdraw ₹500 at the same time from different ATMs.

If the system isn't properly synchronized:

- It checks the balance and sees there’s enough money for both.
- Both transactions go through, even though only one should.
- This results in the account being overdrawn.

#### Run this test

```bash
python test_atm_race_condition.py
```

### 🖨️ Example 2 – Printer Queue (File Writing Interference)

Two users send print jobs simultaneously. Without proper queue management:

- The printer might interleave pages from both documents.
- This leads to mixed-up printouts and data corruption.

#### Run this test

```bash
python test_file_writing_interference.py
```

## 🎯 Commands Overview

| Command | Purpose | Real-time | Output |
|---------|---------|-----------|---------|
| `submit` | Create and submit new job | Optional streaming | Job ID + status |
| `view` | Display job details and output | Optional following | Formatted job info |
| `stream` | Stream live logs from running job | Yes | Real-time logs |
| `cancel` | Stop running job | No | Confirmation |

## 📖 Command Reference

### submit - Submit New Job

Submit a shell command for remote execution.

```bash
python main.py submit [OPTIONS] COMMAND
```

**Arguments:**

- `COMMAND`: Shell command to execute (required)

**Options:**

- `--priority [Low|Medium|High]`: Job execution priority (default: Medium)
- `--timeout INTEGER`: Maximum execution time in seconds, 1-3600 (default: 30)
- `--stream`: Stream logs in real-time after submission
- `--wait`: Wait for job completion before exiting

**Examples:**

```bash
# Basic job submission
python main.py submit "ls -la /home"

# High priority with timeout
python main.py submit "backup-database.sh" --priority High --timeout 1800

# Submit with real-time streaming
python main.py submit "find /var/log -name '*.log'" --stream

# Submit and wait for completion
python main.py submit "system-update.sh" --wait
```

**Output:**

```shell
Submitting job  [####################################]  100%
✅ Job submitted successfully!
Job ID: f489c755-ba8f-4a99-9cd3-ad41834340b4
Status: Queued
```

### view - View Job Details

Display comprehensive job information including status, output, and metadata.

```bash
python main.py view [OPTIONS] JOB_ID
```

**Arguments:**

- `JOB_ID`: UUID of the job to view (required)

**Options:**

- `--format [table|json]`: Output format (default: table)
- `--follow`: Follow job status updates in real-time

**Examples:**

```bash
# View job with formatted table
python main.py view f489c755-ba8f-4a99-9cd3-ad41834340b4

# View job as JSON
python main.py view f489c755-ba8f-4a99-9cd3-ad41834340b4 --format json

# Follow job status in real-time
python main.py view f489c755-ba8f-4a99-9cd3-ad41834340b4 --follow
```

**Table Output:**

```shell
📄 Job Details
──────────────────────────────────────────────────
ID          : f489c755-ba8f-4a99-9cd3-ad41834340b4
Command     : echo 'Hello Remote Jobs!'
Status      : Success
Priority    : High
Timeout     : 30s
Created     : 2025-01-30 17:42:04 UTC
Started     : 2025-01-30 17:42:04 UTC
Completed   : 2025-01-30 17:42:06 UTC
Duration    : 0:00:02.261690

📤 STDOUT:
────────────────────
Hello Remote Jobs!

📥 STDERR: (empty)
```

**JSON Output:**

```json
{
  "id": "f489c755-ba8f-4a99-9cd3-ad41834340b4",
  "command": "echo 'Hello Remote Jobs!'",
  "priority": "High",
  "status": "Success",
  "timeout": 30,
  "stdout": "Hello Remote Jobs!\n",
  "stderr": null,
  "created_at": "2025-01-30T17:42:04.123456Z",
  "started_at": "2025-01-30T17:42:04.234567Z",
  "completed_at": "2025-01-30T17:42:06.496257Z"
}
```

### stream - Real-time Log Streaming

Stream live logs from a running job via WebSocket connection.

```bash
python main.py stream [OPTIONS] JOB_ID
```

**Arguments:**

- `JOB_ID`: UUID of the job to stream (required)

**Options:**

- `--duration INTEGER`: Maximum streaming duration in seconds, 1-86400 (default: 3600)

**Examples:**

```bash
# Stream job logs
python main.py stream f489c755-ba8f-4a99-9cd3-ad41834340b4

# Stream with custom timeout
python main.py stream f489c755-ba8f-4a99-9cd3-ad41834340b4 --duration 7200
```

**Output:**

```shell
📡 Connected to live logs for job f489c755-ba8f-4a99-9cd3-ad41834340b4...

Starting backup process...
Creating temporary directory: /tmp/backup_20250130
Backing up database: production_db
Progress: 25% complete
Progress: 50% complete
Progress: 75% complete
Backup completed successfully
Cleaning up temporary files...

✅ Job completed with status: Success
📡 Log stream finished.
```

**Behavior:**

- Automatically connects to job's WebSocket stream
- Displays logs in real-time as they're generated
- Shows job completion status when finished
- Handles connection errors gracefully
- Supports keyboard interrupt (Ctrl+C) to stop streaming

### cancel - Cancel Running Job

Stop a running job with optional confirmation.

```bash
python main.py cancel [OPTIONS] JOB_ID
```

**Arguments:**

- `JOB_ID`: UUID of the job to cancel (required)

**Options:**

- `--force`: Skip confirmation prompt and cancel immediately

**Examples:**

```bash
# Cancel with confirmation
python main.py cancel f489c755-ba8f-4a99-9cd3-ad41834340b4

# Force cancel without confirmation
python main.py cancel f489c755-ba8f-4a99-9cd3-ad41834340b4 --force
```

**Interactive Cancellation:**

```shell
Job Status: Running
Command: long-running-backup.sh --full --verify...
Are you sure you want to cancel this job? [y/N]: y
🛑 Job cancellation requested successfully
Wait to confirm cancellation? [y/N]: y
Updated status: Cancelled
```

**Force Cancellation:**

```shell
🛑 Job cancellation requested successfully
Wait to confirm cancellation? [y/N]: n
```
