import logging
from uuid import UUID
from dependency_injector.wiring import Provide

from jobs.data.abstract_repo import JobAbstractRepository
from jobs.domain.domain_models import JobDomainModel, JobStatusEnum
from jobs.exceptions import JobCannotBeCancelledException

logger = logging.getLogger(__name__)


class CancelJobUseCase:
    def __init__(
        self,
        db_repo: JobAbstractRepository = Provide["db_repo"],
    ) -> None:
        self.db_repo = db_repo

    def execute(self, job_id: UUID) -> JobDomainModel:
        logger.info("Got request to cancel job with id %s", job_id)
        job = self.db_repo.get(job_id)
        if job.status in [JobStatusEnum.SUCCESS, JobStatusEnum.FAILED, JobStatusEnum.CANCELLED]:
            raise JobCannotBeCancelledException(
                detail=f"Job with status '{job.status}' cannot be cancelled"
            )
        job.status = JobStatusEnum.CANCELLED
        return self.db_repo.update(job, ["status"])
