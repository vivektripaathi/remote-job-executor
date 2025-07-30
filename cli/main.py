import click
import asyncio
import websockets
import json
import sys
import time
from utils import Config, validate_job_id, make_request, handle_api_response, display_job_table

config = Config()

@click.group()
@click.option("--api-url", help="Override API URL")
def cli(api_url):
    if api_url:
        config.base_url = api_url

@cli.command()
@click.argument("command", required=True)
@click.option("--priority", default="Medium", 
                type=click.Choice(["Low", "Medium", "High"], case_sensitive=False),
                help="Priority of the job (Low, Medium, High)")
@click.option("--timeout", default=30, type=click.IntRange(1, 3600), 
                help="Timeout in seconds (1-3600)")
@click.option("--stream", is_flag=True, help="Stream logs in real-time after submission")
@click.option("--wait", is_flag=True, help="Wait for job completion before exiting")
def submit(command, priority, timeout, stream, wait):
    # Input validation
    if not command.strip():
        click.secho("❌ Command cannot be empty", fg="red")
        sys.exit(1)
    
    if len(command) > 1000:
        click.secho("❌ Command too long (max 1000 characters)", fg="red")
        sys.exit(1)
    
    payload = {
        "command": command,
        "priority": priority.title(),
        "timeout": timeout,
        "streaming": stream or wait
    }
    
    with click.progressbar(length=1, label="Submitting job") as bar:
        response = make_request("POST", f"{config.base_url}/", json=payload)
        bar.update(1)
    
    job = handle_api_response(response, f"✅ Job submitted successfully!")
    job_id = job['id']
    
    click.secho(f"Job ID: {job_id}", fg="cyan")
    click.secho(f"Status: {job.get('status', 'Unknown')}", fg="yellow")
    
    if stream:
        click.echo("Waiting for job to start...")
        stream_job_logs(job_id)
    elif wait:
        wait_for_job_completion(job_id)

def stream_job_logs(job_id: str, max_duration: int = 3600):
    async def stream_logs():
        uri = f"{config.ws_url}/{job_id}/"
        timeout_time = time.time() + max_duration
        
        try:
            async with websockets.connect(uri) as websocket:
                click.secho(f"📡 Connected to live logs for job {job_id}...\n", fg="cyan")
                
                while time.time() < timeout_time:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        log = data.get("log", "")
                        if log:
                            print(log, end="")
                        
                        # Check if job is completed
                        if data.get("status") in ["Success", "Failed", "Cancelled"]:
                            click.secho(f"\n✅ Job completed with status: {data.get('status')}", fg="green")
                            break
                            
                    except asyncio.TimeoutError:
                        continue  # Keep trying
                        
                click.secho("\n📡 Log stream finished.", fg="green")
                
        except websockets.exceptions.ConnectionClosed:
            click.secho("\n✅ Job log stream finished.", fg="green")
        except websockets.exceptions.InvalidURI:
            click.secho(f"❌ Invalid WebSocket URI: {uri}", fg="red")
        except Exception as e:
            click.secho(f"❌ WebSocket error: {e}", fg="red")
    
    try:
        asyncio.run(stream_logs())
    except KeyboardInterrupt:
        click.secho("\n🛑 Log streaming interrupted by user", fg="yellow")

def wait_for_job_completion(job_id: str, poll_interval: int = 2, max_wait: int = 3600):
    start_time = time.time()
    
    with click.progressbar(length=max_wait, label="Waiting for completion") as bar:
        while time.time() - start_time < max_wait:
            try:
                response = make_request("GET", f"{config.base_url}/{job_id}/")
                job = handle_api_response(response)
                
                status = job.get('status', 'Unknown')
                if status in ['Success', 'Failed', 'Cancelled']:
                    bar.finish()
                    click.secho(f"\n✅ Job completed with status: {status}", fg="green")
                    
                    if job.get('stdout'):
                        click.secho("\n📤 STDOUT:", fg="green")
                        click.echo(job['stdout'])
                    
                    if job.get('stderr'):
                        click.secho("\n📥 STDERR:", fg="red")  
                        click.echo(job['stderr'])
                    
                    return
                
                elapsed = int(time.time() - start_time)
                bar.update(min(elapsed, max_wait))
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                click.secho("\n🛑 Wait interrupted by user", fg="yellow")
                return
    
    click.secho(f"\n⏰ Timeout after {max_wait} seconds", fg="yellow")

@cli.command()
@click.argument("job_id", required=True)
@click.option("--format", "-f", type=click.Choice(["table", "json"]), 
                default="table", help="Output format")
@click.option("--follow", is_flag=True, help="Follow job status updates")
def view(job_id, format, follow):
    # Validate job ID format
    if not validate_job_id(job_id):
        click.secho("❌ Invalid job ID format (expected UUID)", fg="red")
        sys.exit(1)
    
    if follow:
        follow_job_status(job_id)
        return
    
    response = make_request("GET", f"{config.base_url}/{job_id}/")
    job = handle_api_response(response, "✅ Job details retrieved")
    
    if format == "json":
        click.echo(json.dumps(job, indent=2))
    else:
        display_job_table(job)

def follow_job_status(job_id: str, poll_interval: int = 2):
    click.secho(f"📡 Following job {job_id} (Ctrl+C to stop)...\n", fg="cyan")
    
    last_status = None
    try:
        while True:
            response = make_request("GET", f"{config.base_url}/{job_id}/")
            job = handle_api_response(response)
            
            current_status = job.get('status')
            if current_status != last_status:
                timestamp = time.strftime("%H:%M:%S")
                click.secho(f"[{timestamp}] Status: {current_status}", fg="yellow")
                last_status = current_status
                
                if current_status in ['Success', 'Failed', 'Cancelled']:
                    click.secho(f"\n✅ Job finished with status: {current_status}", fg="green")
                    display_job_table(job)
                    break
            
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        click.secho("\n🛑 Status following stopped by user", fg="yellow")

@cli.command()
@click.argument("job_id", required=True)  
@click.option("--force", is_flag=True, help="Force cancellation without confirmation")
def cancel(job_id, force):
    # Validate job ID format
    if not validate_job_id(job_id):
        click.secho("❌ Invalid job ID format (expected UUID)", fg="red")
        sys.exit(1)
    
    # Get job status first
    try:
        response = make_request("GET", f"{config.base_url}/{job_id}/")
        job = handle_api_response(response)
        current_status = job.get('status')
        
        if current_status in ['Success', 'Failed', 'Cancelled']:
            click.secho(f"ℹ️  Job is already {current_status.lower()}, nothing to cancel", fg="blue")
            return
        
        if not force:
            click.secho(f"Job Status: {current_status}", fg="yellow")
            click.secho(f"Command: {job.get('command', 'Unknown')[:60]}...", fg="yellow")
            if not click.confirm("Are you sure you want to cancel this job?"):
                click.secho("Cancellation aborted", fg="blue")
                return
    
    except Exception as e:
        if not force:
            click.secho(f"⚠️  Could not verify job status: {e}", fg="yellow") 
            if not click.confirm("Continue with cancellation anyway?"):
                return
    
    response = make_request("POST", f"{config.base_url}/{job_id}/cancel/")
    handle_api_response(response, "🛑 Job cancellation requested successfully")
    
    # Optionally wait to confirm cancellation
    if click.confirm("Wait to confirm cancellation?", default=False):
        response = make_request("GET", f"{config.base_url}/{job_id}/")
        job = handle_api_response(response)
        click.secho(f"Job status updated to: {job.get('status')}", fg="cyan")

@cli.command()  
@click.argument("job_id", required=True)
@click.option("--duration", "-d", default=3600, type=click.IntRange(1, 86400),
                help="Maximum streaming duration in seconds (default: 3600)")
def stream(job_id, duration):
    # Validate job ID format
    if not validate_job_id(job_id):
        click.secho("❌ Invalid job ID format (expected UUID)", fg="red")
        sys.exit(1)
    
    # Check if job exists and is streamable
    try:
        response = make_request("GET", f"{config.base_url}/{job_id}/")
        job = handle_api_response(response)
        status = job.get('status')
        
        if status in ['Success', 'Failed', 'Cancelled']:
            click.secho(f"ℹ️  Job is already {status.lower()}, showing final output:", fg="blue")
            display_job_table(job)
            return
        
        click.secho(f"Job Status: {status}", fg="yellow")
        
    except Exception as e:
        click.secho(f"⚠️  Could not verify job status: {e}", fg="yellow")
        if not click.confirm("Continue with streaming anyway?"):
            return
    
    stream_job_logs(job_id, duration)

def main():
    try:
        cli()
    except KeyboardInterrupt:
        click.secho("\n🛑 Operation cancelled by user", fg="yellow")
        sys.exit(130)
    except Exception as e:
        click.secho(f"❌ Unexpected error: {e}", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    main()
