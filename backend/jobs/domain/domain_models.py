from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from enum import Enum


class JobStatusEnum(str, Enum):
    QUEUED = "Queued"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class JobPriorityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class JobDomainModel(BaseModel):
    id: Optional[UUID] = None
    command: str
    timeout: int = 60
    priority: JobPriorityEnum = JobPriorityEnum.MEDIUM
    status: JobStatusEnum = JobStatusEnum.QUEUED
    parameters: Optional[dict] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_id: Optional[str] = None
    remote_process_id: Optional[str] = None

    class Config:
        orm_mode = True


class JobCreateRequest(BaseModel):
    command: str
    timeout: int = 60
    priority: JobPriorityEnum = JobPriorityEnum.MEDIUM
    parameters: Optional[dict] = None
    streaming: Optional[bool] = False


class JobUpdateRequest(BaseModel):
    command: Optional[str] = None
    timeout: Optional[int] = None
    priority: Optional[JobPriorityEnum] = None
    status: Optional[JobStatusEnum] = None
    parameters: Optional[dict] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_id: Optional[str] = None
    remote_process_id: Optional[str] = None

    def is_any_field_set(self, field_name: str) -> bool:
        """Check if a field is explicitly set in the request"""
        return hasattr(self, field_name) and getattr(self, field_name) is not None


class JobListDomainModel(BaseModel):
    """Domain model for job list operations"""
    __root__: List[JobDomainModel]

    def dict_serialized(self) -> dict:
        """Serialize to dict for JSON response"""
        return {"jobs": [job.dict() for job in self.__root__]}


class JobListRequest(BaseModel):
    """Request model for listing jobs with pagination"""
    limit: Optional[int] = None
    offset: Optional[int] = None
