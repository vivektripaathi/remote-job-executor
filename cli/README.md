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
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 2. Install CLI Dependencies

```bash
# From CLI directory
cd cli
pip3 install -r requirements.txt
```

**Dependencies installed:**

- `click==8.1.8` - Command-line interface framework
- `requests==2.32.4` - HTTP client for API calls
- `websockets==15.0.1` - WebSocket client for real-time streaming

### 3. Configure Environment (Optional)

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

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# API Endpoints
REMOTE_JOB_API_URL=http://localhost:8000/jobs
REMOTE_JOB_WS_URL=ws://localhost:8000/ws/jobs

# Production Example:
# REMOTE_JOB_API_URL=https://api.yourcompany.com/jobs
# REMOTE_JOB_WS_URL=wss://api.yourcompany.com/ws/jobs
```

### Runtime Configuration

```bash
# Override API URL for single command
python main.py --api-url https://staging-api.com/jobs submit "test command"
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

## 🎨 Output Features

### Status Color Coding

- 🟢 **Success**: Green
- 🔴 **Failed**: Red  
- 🟡 **Running**: Yellow
- 🔵 **Queued**: Blue
- 🟣 **Cancelled**: Magenta

### Progress Indicators

- Animated progress bars for job submission
- Real-time status updates during streaming
- Duration calculations for completed jobs
- Timestamp formatting with timezone

### Error Handling

- Detailed error messages with context
- HTTP status code interpretation
- WebSocket connection error handling
- Input validation with helpful feedback

## 🔧 Advanced Usage

### Environment Switching

```bash
# Development environment
export REMOTE_JOB_API_URL=http://localhost:8000/jobs
python main.py submit "dev-test.sh"

# Staging environment  
export REMOTE_JOB_API_URL=https://staging-api.com/jobs
python main.py submit "staging-test.sh"

# Production environment
export REMOTE_JOB_API_URL=https://api.production.com/jobs
python main.py submit "prod-deploy.sh" --priority High
```

### Job Workflow Examples

**Database Backup Workflow:**

```bash
# Submit backup job with high priority
JOB_ID=$(python main.py submit "backup-database.sh --full" --priority High --format json | jq -r '.id')

# Monitor progress
python main.py stream $JOB_ID

# Check final results
python main.py view $JOB_ID
```

**Long-running Process Management:**

```bash
# Start long-running job
JOB_ID=$(python main.py submit "data-migration.py --batch-size 1000" --timeout 3600 | grep "Job ID:" | cut -d: -f2 | tr -d ' ')

# Follow in another terminal
python main.py view $JOB_ID --follow

# Cancel if needed
python main.py cancel $JOB_ID --force
```

**Batch Job Processing:**

```bash
#!/bin/bash
# batch-submit.sh
commands=(
    "process-file-1.sh"
    "process-file-2.sh"  
    "process-file-3.sh"
)

for cmd in "${commands[@]}"; do
    echo "Submitting: $cmd"
    python main.py submit "$cmd" --priority Medium
    sleep 1
done
```

### Scripting Integration

**Bash Integration:**

```bash
#!/bin/bash
# Example: Automated deployment script

echo "Starting deployment..."

# Submit deployment job
JOB_ID=$(python main.py submit "deploy.sh --env=production" \
    --priority High --timeout 1800 --format json | jq -r '.id')

if [ $? -eq 0 ]; then
    echo "Deployment job submitted: $JOB_ID"
    
    # Wait for completion
    python main.py view $JOB_ID --follow
    
    # Check final status
    STATUS=$(python main.py view $JOB_ID --format json | jq -r '.status')
    
    if [ "$STATUS" = "Success" ]; then
        echo "✅ Deployment completed successfully"
        exit 0
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "❌ Failed to submit deployment job"
    exit 1
fi
```

**Python Integration:**

```python
#!/usr/bin/env python3
# Example: Python automation script

import subprocess
import json
import sys

def submit_job(command, priority="Medium", timeout=30):
    """Submit job and return job data"""
    cmd = [
        "python", "main.py", "submit", command,
        "--priority", priority,
        "--timeout", str(timeout),
        "--format", "json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        print(f"Error: {result.stderr}")
        return None

def wait_for_job(job_id):
    """Wait for job completion and return final status"""
    cmd = ["python", "main.py", "view", job_id, "--format", "json"]
    
    while True:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            job_data = json.loads(result.stdout)
            status = job_data['status']
            
            if status in ['Success', 'Failed', 'Cancelled']:
                return status
            
            time.sleep(2)
        else:
            return None

# Usage example
if __name__ == "__main__":
    job = submit_job("backup-system.sh", priority="High", timeout=1800)
    if job:
        print(f"Job submitted: {job['id']}")
        final_status = wait_for_job(job['id'])
        print(f"Final status: {final_status}")
```

## 🛡️ Error Handling

### Connection Errors

```bash
❌ Request failed: HTTPConnectionPool(host='localhost', port=8000): 
   Max retries exceeded with url: /jobs/
```

**Solution**: Verify backend server is running and API URL is correct.

### Invalid Job ID

```bash
❌ Invalid job ID format (expected UUID)
```

**Solution**: Ensure job ID is a valid UUID format.

### WebSocket Errors

```bash
❌ WebSocket error: Connection refused
```

**Solution**: Check WebSocket URL and ensure Channels/Redis are running.

### Timeout Errors

```bash
❌ Request failed: Read timeout
```

**Solution**: Increase timeout or check server performance.

## 🔍 Troubleshooting

### Debug Mode

Set environment variable for verbose output:

```bash
export PYTHONPATH=.
python -u main.py submit "test command"
```

### Network Connectivity

Test API connectivity:

```bash
curl -X GET http://localhost:8000/jobs/list/
```

Test WebSocket connectivity:

```bash
# Using wscat (npm install -g wscat)
wscat -c ws://localhost:8000/ws/jobs/test-id/
```

### Configuration Issues

Verify environment file:

```bash
cat .env
python -c "from utils import Config; c=Config(); print(f'API: {c.base_url}'); print(f'WS: {c.ws_url}')"
```

## 📊 Performance Tips

### Efficient Job Management

- Use `--format json` for programmatic access
- Batch job submissions with appropriate delays
- Use `--force` flag for automated cancellations
- Monitor job duration to set appropriate timeouts

### Resource Usage

- Close streaming connections when not needed
- Use appropriate timeout values for different job types
- Avoid polling job status too frequently
- Use WebSocket streaming instead of repeated API calls

## 🔐 Security Considerations

- Store API credentials in environment files, not scripts
- Use HTTPS/WSS in production environments
- Validate job IDs before processing
- Implement proper timeout values
- Monitor for unauthorized access patterns

This CLI provides a comprehensive interface for remote job management with production-ready features and extensive customization options.
