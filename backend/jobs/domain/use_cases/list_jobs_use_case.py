import logging
from typing import List, Optional
from dependency_injector.wiring import Provide

from jobs.data.abstract_repo import JobAbstractRepository
from jobs.domain.domain_models import JobDomainModel

logger = logging.getLogger(__name__)


class JobListResponse:
    def __init__(self, jobs: List[JobDomainModel], total_count: int):
        self.jobs = jobs
        self.total_count = total_count


class ListJobsUseCase:
    def __init__(
        self,
        db_repo: JobAbstractRepository = Provide["db_repo"],
    ) -> None:
        self.db_repo = db_repo

    def execute(self, limit: Optional[int] = None, offset: Optional[int] = None) -> JobListResponse:
        logger.info("Got request to list jobs with limit %s and offset %s", limit, offset)
        jobs = self.db_repo.list(limit=limit, offset=offset)
        total_count = self.db_repo.count()
        return JobListResponse(
            jobs=jobs,
            total_count=total_count
        )
