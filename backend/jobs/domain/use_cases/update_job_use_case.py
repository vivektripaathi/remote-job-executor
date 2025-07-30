import logging
from typing import List, Tuple
from uuid import UUID
from dependency_injector.wiring import Provide

from jobs.data.abstract_repo import JobAbstractRepository
from jobs.domain.domain_models import JobDomainModel, JobUpdateRequest

logger = logging.getLogger(__name__)


class UpdateJobUseCase:
    def __init__(
        self,
        db_repo: JobAbstractRepository = Provide["db_repo"],
    ) -> None:
        self.db_repo = db_repo

    def _check_if_field_is_set_and_update(
        self,
        field_name: str,
        update_request: JobUpdateRequest,
        job_domain: JobDomainModel,
    ) -> Tuple[JobDomainModel, bool]:
        if update_request.is_any_field_set(field_name):
            update_field_value = getattr(update_request, field_name)
            logger.info(
                "Updating %s of job with id %s from '%s' to '%s'",
                field_name,
                job_domain.id,
                getattr(job_domain, field_name),
                update_field_value,
            )
            setattr(job_domain, field_name, update_field_value)
            return job_domain, True
        return job_domain, False

    def _update_job_fields(
        self,
        update_request: JobUpdateRequest,
        job_domain: JobDomainModel,
    ) -> JobDomainModel:
        update_fields: List[str] = []
        
        for field in [
            "command",
            "timeout", 
            "priority",
            "status",
            "parameters",
            "stdout",
            "stderr",
            "started_at",
            "completed_at",
            "task_id",
            "remote_process_id",
        ]:
            job_domain, is_updated = self._check_if_field_is_set_and_update(
                field, update_request, job_domain
            )
            if is_updated:
                update_fields.append(field)

        if len(update_fields) > 0:
            logger.info(
                "Updating fields %s of job with id %s",
                update_fields,
                job_domain.id,
            )
            job_domain = self.db_repo.update(job_domain, update_fields)
        
        return job_domain

    def execute(self, job_id: UUID, update_request: JobUpdateRequest) -> JobDomainModel:
        logger.info("Got request to update job with id %s", job_id)
        job_domain = self.db_repo.get(job_id)
        return self._update_job_fields(update_request, job_domain)
