from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from jobs.domain.domain_models import JobDomainModel, JobStatusEnum, JobPriorityEnum


class JobResponse(BaseModel):
    """Response model for Job API endpoints"""
    id: UUID
    command: str
    timeout: int
    priority: JobPriorityEnum
    status: JobStatusEnum
    parameters: Optional[dict]
    stdout: Optional[str]
    stderr: Optional[str]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    task_id: Optional[str]
    remote_process_id: Optional[str]

    @classmethod
    def from_orm(cls, job_domain: JobDomainModel) -> "JobResponse":
        """Convert domain model to response"""
        return cls(
            id=job_domain.id,
            command=job_domain.command,
            timeout=job_domain.timeout,
            priority=job_domain.priority,
            status=job_domain.status,
            parameters=job_domain.parameters,
            stdout=job_domain.stdout,
            stderr=job_domain.stderr,
            created_at=job_domain.created_at,
            modified_at=job_domain.modified_at,
            started_at=job_domain.started_at,
            completed_at=job_domain.completed_at,
            task_id=job_domain.task_id,
            remote_process_id=job_domain.remote_process_id,
        )

    def dict_serialized(self) -> dict:
        """Serialize to dict for JSON response"""
        return self.dict()


class JobListResponse(BaseModel):
    """Response model for job list endpoints"""
    jobs: List[JobResponse]
    total_count: int

    @classmethod
    def from_domain_list(cls, jobs: List[JobDomainModel], total_count: int) -> "JobListResponse":
        """Convert list of domain models to response"""
        return cls(
            jobs=[JobResponse.from_orm(job) for job in jobs],
            total_count=total_count
        )

    def dict_serialized(self) -> dict:
        """Serialize to dict for JSON response"""
        return self.dict()
