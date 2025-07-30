import logging
from uuid import UUID
from dependency_injector.wiring import Provide

from jobs.data.abstract_repo import JobAbstractRepository

logger = logging.getLogger(__name__)


class DeleteJobUseCase:
    def __init__(
        self,
        db_repo: JobAbstractRepository = Provide["db_repo"],
    ) -> None:
        self.db_repo = db_repo

    def execute(self, job_id: UUID) -> None:
        logger.info("Got request to delete job with id %s", job_id)
        self.db_repo.delete(job_id)
