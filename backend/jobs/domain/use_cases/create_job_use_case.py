import logging
import uuid
from dependency_injector.wiring import Provide

from jobs.data.abstract_repo import JobAbstractRepository
from jobs.domain.domain_models import JobDomainModel, JobCreateRequest

logger = logging.getLogger(__name__)


class CreateJobUseCase:
    def __init__(
        self,
        db_repo: JobAbstractRepository = Provide["db_repo"],
    ) -> None:
        self.db_repo = db_repo

    def execute(self, create_request: JobCreateRequest) -> JobDomainModel:
        logger.info("Got request to create a new job")
        job_domain = JobDomainModel(
            id=uuid.uuid4(),
            command=create_request.command,
            timeout=create_request.timeout,
            priority=create_request.priority,
            parameters=create_request.parameters,
        )
        created_job = self.db_repo.create(job_domain)
        try:
            if create_request.streaming:
                from jobs.tasks import run_job_streaming
                run_job_streaming.delay(str(created_job.id))
                logger.info(f"Job {created_job.id} queued for streaming execution")
            else:
                from jobs.tasks import run_job
                run_job.delay(str(created_job.id))
                logger.info(f"Job {created_job.id} queued for execution")
        except Exception as e:
            logger.error(f"Failed to queue job {created_job.id}: {e}")
        return created_job
