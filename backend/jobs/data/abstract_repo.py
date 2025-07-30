import abc
from typing import List, Optional
from uuid import UUID

from jobs.domain.domain_models import JobDomainModel, JobCreateRequest, JobUpdateRequest


class JobAbstractRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, job_domain: JobDomainModel) -> JobDomainModel:
        """Create a new job"""

    @abc.abstractmethod
    def get(self, job_id: UUID) -> JobDomainModel:
        """Get a job by id"""

    @abc.abstractmethod
    def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[JobDomainModel]:
        """List all jobs with optional pagination"""

    @abc.abstractmethod
    def update(self, job_domain: JobDomainModel, update_fields: List[str]) -> JobDomainModel:
        """Update a job with specific fields"""

    @abc.abstractmethod
    def delete(self, job_id: UUID) -> None:
        """Delete a job"""

    @abc.abstractmethod
    def count(self) -> int:
        """Get total count of jobs"""
