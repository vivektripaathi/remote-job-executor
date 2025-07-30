from django.utils import timezone
from jobs.models import Job
from celery import shared_task
from celery.utils.log import get_task_logger
from dependency_injector.wiring import Provide, inject
from asgiref.sync import async_to_sync

from jobs.domain.use_cases.execute_remote_command_use_case import ExecuteRemoteCommandUseCase
from jobs.domain.use_cases.execute_remote_command_streaming_use_case import ExecuteRemoteCommandStreamingUseCase
from jobs.domain.use_cases.kill_remote_process_use_case import KillRemoteProcessUseCase

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, retry_backoff=30)
@inject
def run_job(
    self,
    job_id,
    execute_use_case: ExecuteRemoteCommandUseCase = Provide["execute_remote_command_use_case"],
):
    logger.info("Task called to run job with id %s request id: %s", job_id, self.request.id)
    
    job = Job.objects.get(id=job_id)
    job.status = "Running"
    job.started_at = timezone.now()
    job.save()

    try:
        stdout, stderr = execute_use_case.execute(job.command, timeout=job.timeout)
        job.stdout = stdout
        job.stderr = stderr
        job.status = "Success" if not stderr else "Failed"
        logger.info("Job %s completed successfully with status %s", job_id, job.status)
    except Exception as e:
        job.stderr = str(e)
        job.status = "Failed"
        logger.error("Job %s failed with error: %s", job_id, str(e))
        if self.request.retries < self.max_retries:
            logger.info("Retrying job %s (attempt %d/%d)", job_id, self.request.retries + 1, self.max_retries)
            self.retry()
    finally:
        job.completed_at = timezone.now()
        job.save()
    
    return {"job_id": job_id, "status": job.status}

@shared_task(bind=True, max_retries=3, retry_backoff=30)
@inject
def run_job_streaming(
    self,
    job_id,
    streaming_use_case: ExecuteRemoteCommandStreamingUseCase = Provide["execute_remote_command_streaming_use_case"],
):
    logger.info("Task called to run streaming job with id %s request id: %s", job_id, self.request.id)
    
    job = Job.objects.get(id=job_id)
    job.status = "Running"
    job.started_at = timezone.now()
    job.save()

    try:
        stdout, stderr = async_to_sync(streaming_use_case.execute)(str(job.id), job.command, timeout=job.timeout)
        job.stdout = stdout
        job.stderr = stderr
        job.status = "Success" if not stderr else "Failed"
        logger.info("Streaming job %s completed successfully with status %s", job_id, job.status)
    except TimeoutError as e:
        job.stderr = str(e)
        job.status = "Failed"
        logger.error("Streaming job %s timed out: %s", job_id, str(e))
        if self.request.retries < self.max_retries:
            logger.info("Retrying streaming job %s (attempt %d/%d)", job_id, self.request.retries + 1, self.max_retries)
            self.retry()
    except Exception as e:
        job.stderr = str(e)
        job.status = "Failed"
        logger.error("Streaming job %s failed with error: %s", job_id, str(e))
        if self.request.retries < self.max_retries:
            logger.info("Retrying streaming job %s (attempt %d/%d)", job_id, self.request.retries + 1, self.max_retries)
            self.retry()
    finally:
        job.completed_at = timezone.now()
        job.save()
    
    return {"job_id": job_id, "status": job.status}

@shared_task(bind=True, max_retries=3, retry_backoff=30)
@inject
def cancel_job(
    self,
    job_id,
    kill_use_case: KillRemoteProcessUseCase = Provide["kill_remote_process_use_case"],
):
    from celery import current_app
    
    logger.info("Task called to cancel job with id %s request id: %s", job_id, self.request.id)

    job = Job.objects.get(id=job_id)

    if job.task_id:
        logger.info("Revoking Celery task %s for job %s", job.task_id, job_id)
        current_app.control.revoke(job.task_id, terminate=True, signal="SIGKILL")

    if job.remote_process_id:
        try:
            logger.info("Killing remote process %s for job %s", job.remote_process_id, job_id)
            kill_use_case.execute(job.remote_process_id)
        except Exception as e:
            error_msg = f"Failed to kill remote process: {e}"
            job.stderr = f"{job.stderr}\n{error_msg}" if job.stderr else error_msg
            logger.error("Failed to kill remote process %s for job %s: %s", job.remote_process_id, job_id, str(e))

    job.status = "Cancelled"
    job.completed_at = timezone.now()
    job.save()
    
    logger.info("Job %s cancelled successfully", job_id)
    return {"job_id": job_id, "status": job.status}
