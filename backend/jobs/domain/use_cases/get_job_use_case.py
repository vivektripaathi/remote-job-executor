import logging
from uuid import UUID
from dependency_injector.wiring import Provide

from jobs.data.abstract_repo import JobAbstractRepository
from jobs.domain.domain_models import JobDomainModel

logger = logging.getLogger(__name__)


class GetJobUseCase:
    def __init__(
        self,
        db_repo: JobAbstractRepository = Provide["db_repo"],
    ) -> None:
        self.db_repo = db_repo

    def execute(self, job_id: UUID) -> JobDomainModel:
        logger.info("Got request to get job with id %s", job_id)
        return self.db_repo.get(job_id)
