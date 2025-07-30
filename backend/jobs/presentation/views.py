from uuid import UUID
import pydantic
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dependency_injector.wiring import Provide
from pydantic import ValidationError

from jobs.domain.use_cases.create_job_use_case import CreateJobUseCase
from jobs.domain.use_cases.get_job_use_case import GetJobUseCase
from jobs.domain.use_cases.list_jobs_use_case import ListJobsUseCase
from jobs.domain.use_cases.update_job_use_case import UpdateJobUseCase
from jobs.domain.use_cases.cancel_job_use_case import CancelJobUseCase
from jobs.domain.use_cases.delete_job_use_case import DeleteJobUseCase
from jobs.domain.domain_models import JobCreateRequest, JobUpdateRequest
from jobs.presentation.types import JobResponse, JobListResponse
from jobs.types import JobId


class CreateJobView(APIView):
    def post(
        self,
        request,
        create_job_use_case: CreateJobUseCase = Provide["create_job_use_case"]
    ):
        """Create a new job"""
        try:
            # Apply proper request validation with pydantic parse_obj_as
            create_request = pydantic.parse_obj_as(JobCreateRequest, request.data)
        except ValidationError as e:
            return Response(
                {"error": "Validation failed", "details": e.errors()},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job = create_job_use_case.execute(create_request)
        response = JobResponse.from_orm(job)
        return Response(response.dict_serialized(), status=status.HTTP_201_CREATED)


class GetUpdateDeleteJobView(APIView):
    def get(
        self,
        request,
        job_id: JobId,
        get_job_use_case: GetJobUseCase = Provide["get_job_use_case"],
    ):
        """Get a specific job by ID"""
        job = get_job_use_case.execute(job_id)
        response = JobResponse.from_orm(job)
        return Response(data=response.dict_serialized(), status=status.HTTP_200_OK)

    def patch(
        self,
        request,
        job_id: JobId,
        update_job_use_case: UpdateJobUseCase = Provide["update_job_use_case"],
    ):
        """Update a job"""
        try:
            update_request = JobUpdateRequest.parse_obj(request.data)
        except ValidationError as e:
            return Response(
                {"error": "Validation failed", "details": e.errors()},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_job = update_job_use_case.execute(job_id, update_request)
        response = JobResponse.from_orm(updated_job)
        return Response(data=response.dict_serialized(), status=status.HTTP_200_OK)

    def delete(
        self,
        request,
        job_id: JobId,
        delete_job_use_case: DeleteJobUseCase = Provide["delete_job_use_case"],
    ):
        """Delete a job"""
        delete_job_use_case.execute(job_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListJobsView(APIView):
    def get(
        self,
        request,
        list_jobs_use_case: ListJobsUseCase = Provide["list_jobs_use_case"],
    ):
        """List all jobs with optional pagination"""
        # Parse and validate query parameters like in CopyJournalTemplateView
        limit = pydantic.parse_obj_as(int, request.query_params.get('limit')) if request.query_params.get('limit') else None
        offset = pydantic.parse_obj_as(int, request.query_params.get('offset')) if request.query_params.get('offset') else None
            
        jobs_response = list_jobs_use_case.execute(limit=limit, offset=offset)
        # Convert domain response to presentation response
        response = JobListResponse.from_domain_list(
            jobs_response.jobs, 
            jobs_response.total_count
        )
        return Response(data=response.dict_serialized(), status=status.HTTP_200_OK)


class CancelJobView(APIView):
    def post(
        self,
        request,
        job_id: JobId,
        cancel_job_use_case: CancelJobUseCase = Provide["cancel_job_use_case"],
    ):
        """Cancel a job"""
        cancelled_job = cancel_job_use_case.execute(job_id)
        response = JobResponse.from_orm(cancelled_job)
        return Response(data=response.dict_serialized(), status=status.HTTP_200_OK)
