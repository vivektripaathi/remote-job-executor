import click
import requests
import json
import sys
import uuid
import os
from typing import Optional, Dict, Any


class Config:
    def __init__(self):
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ.setdefault(key, value)

        self.base_url = os.getenv("REMOTE_JOB_API_URL", "http://localhost:8000/jobs")
        self.ws_url = os.getenv("REMOTE_JOB_WS_URL", "ws://localhost:8000/ws/jobs")


def validate_job_id(job_id: str) -> bool:
    """Validate job ID format (UUID)."""
    if job_id is None:
        return False
    try:
        uuid.UUID(job_id)
        return True
    except (ValueError, TypeError):
        return False


def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request with basic error handling."""
    kwargs.setdefault("timeout", 30)
    kwargs.setdefault("headers", {"Content-Type": "application/json"})
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
        
    except requests.exceptions.RequestException as e:
        click.secho(f"❌ Request failed: {e}", fg="red")
        sys.exit(1)


def handle_api_response(response: requests.Response, success_message: str = None) -> Optional[Dict[Any, Any]]:
    """Handle API response with proper error handling."""
    try:
        if response.status_code in [200, 201]:
            if success_message:
                click.secho(success_message, fg="green")
            return response.json() if response.content else None
        elif response.status_code == 400:
            error_data = response.json() if response.content else {}
            click.secho("❌ Bad Request:", fg="red")
            if "error" in error_data:
                click.echo(f"   {error_data['error']}")
            if "details" in error_data:
                for detail in error_data.get("details", []):
                    click.echo(f"   - {detail.get('msg', detail)}")
        elif response.status_code == 404:
            click.secho("❌ Resource not found", fg="red")
        elif response.status_code == 500:
            click.secho("❌ Server error - please try again later", fg="red")
        else:
            click.secho(f"❌ Request failed with status {response.status_code}", fg="red")
            click.echo(response.text)
        
        sys.exit(1)
    except json.JSONDecodeError:
        click.secho("❌ Invalid response from server", fg="red")
        sys.exit(1)


def format_timestamp(timestamp: Optional[str]) -> str:
    """Format timestamp for display."""
    if not timestamp:
        return "(not set)"
    
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return timestamp


def display_job_table(job: Dict[str, Any]):
    """Display job information in a nice table format."""
    click.secho(f"\n📄 Job Details", bold=True, fg="cyan")
    click.echo("─" * 50)
    
    # Basic info
    click.echo(f"{'ID':<12}: {job['id']}")
    click.echo(f"{'Command':<12}: {job['command'][:60]}{'...' if len(job['command']) > 60 else ''}")
    
    # Status with color coding
    status = job['status']
    status_color = {
        'Success': 'green',
        'Failed': 'red', 
        'Running': 'yellow',
        'Queued': 'blue',
        'Cancelled': 'magenta'
    }.get(status, 'white')
    
    click.echo(f"{'Status':<12}: ", nl=False)
    click.secho(f"{status}", fg=status_color)
    
    click.echo(f"{'Priority':<12}: {job['priority']}")
    click.echo(f"{'Timeout':<12}: {job['timeout']}s")
    
    # Timestamps
    click.echo(f"{'Created':<12}: {format_timestamp(job.get('created_at'))}")
    click.echo(f"{'Started':<12}: {format_timestamp(job.get('started_at'))}")  
    click.echo(f"{'Completed':<12}: {format_timestamp(job.get('completed_at'))}")
    
    # Calculate duration
    if job.get('started_at') and job.get('completed_at'):
        from datetime import datetime
        try:
            start = datetime.fromisoformat(job['started_at'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(job['completed_at'].replace('Z', '+00:00'))
            duration = end - start
            click.echo(f"{'Duration':<12}: {duration}")
        except:
            pass
    
    # Output sections
    if job.get("stdout"):
        click.echo("\n📤 STDOUT:")
        click.echo("─" * 20)
        click.secho(job["stdout"], fg="green")
    else:
        click.echo("\n📤 STDOUT: (empty)")
    
    if job.get("stderr"):
        click.echo("\n📥 STDERR:")
        click.echo("─" * 20)
        click.secho(job["stderr"], fg="red")
    else:
        click.echo("\n📥 STDERR: (empty)")
