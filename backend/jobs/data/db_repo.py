import logging
from typing import List, Optional
from uuid import UUID
from django.db import IntegrityError
from django.utils import timezone

from jobs.data.abstract_repo import JobAbstractRepository
from jobs.domain.domain_models import JobDomainModel
from jobs.exceptions import JobAlreadyExistsException, JobDoesNotExistException
from jobs.models import Job

logger = logging.getLogger(__name__)


class JobDbRepository(JobAbstractRepository):
    def create(self, job_domain: JobDomainModel) -> JobDomainModel:
        """Create a new job (ATOMIC_REQUESTS handles transaction)"""
        logger.info(
            "Creating a new job with command: %s",
            job_domain.command,
        )
        try:
            job_db_entry = Job.objects.create(
                id=job_domain.id,
                command=job_domain.command,
                timeout=job_domain.timeout,
                priority=job_domain.priority.value,
                parameters=job_domain.parameters,
                status=job_domain.status.value,
                created_at=timezone.now(),
                modified_at=timezone.now(),
            )
            return JobDomainModel.from_orm(job_db_entry)
        except IntegrityError as exc:
            raise JobAlreadyExistsException from exc

    def get(self, job_id: UUID) -> JobDomainModel:
        """Get a job by id"""
        try:
            job_db_entry = Job.objects.get(id=job_id)
            return JobDomainModel.from_orm(job_db_entry)
        except Job.DoesNotExist as exc:
            raise JobDoesNotExistException from exc

    def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[JobDomainModel]:
        """List all jobs with optional pagination"""
        queryset = Job.objects.all().order_by('-created_at')
        
        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]
            
        return [JobDomainModel.from_orm(job) for job in queryset]

    def update(self, job_domain: JobDomainModel, update_fields: List[str]) -> JobDomainModel:
        """Update a job with specific fields and race condition protection"""
        logger.info(
            "Updating job %s with fields %s",
            job_domain.id,
            update_fields,
        )
        try:
            job_db_entry = Job.objects.select_for_update().get(id=job_domain.id)
            
            for field in update_fields:
                if field in [
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
                    logger.info(
                        "Updating field %s of job %s",
                        field,
                        job_domain.id,
                    )
                    field_value = getattr(job_domain, field)
                    if field == 'status' and field_value:
                        setattr(job_db_entry, field, field_value.value if hasattr(field_value, 'value') else field_value)
                    else:
                        setattr(job_db_entry, field, field_value)
            
            job_db_entry.modified_at = timezone.now()
            job_db_entry.save()
            
            return JobDomainModel.from_orm(job_db_entry)
        except Job.DoesNotExist as exc:
            raise JobDoesNotExistException from exc

    def delete(self, job_id: UUID) -> None:
        """Delete a job"""
        logger.info("Deleting job %s", job_id)
        try:
            job_db_entry = Job.objects.select_for_update().get(id=job_id)
            job_db_entry.delete()
        except Job.DoesNotExist as exc:
            raise JobDoesNotExistException from exc

    def count(self) -> int:
        """Get total count of jobs"""
        return Job.objects.count()

    def get_with_lock(self, job_id: UUID) -> JobDomainModel:
        """Get a job with database lock for safe updates"""
        try:
            job_db_entry = Job.objects.select_for_update().get(id=job_id)
            return JobDomainModel.from_orm(job_db_entry)
        except Job.DoesNotExist as exc:
            raise JobDoesNotExistException from exc
