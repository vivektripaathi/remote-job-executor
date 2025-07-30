from dependency_injector import containers, providers

from jobs.data.abstract_repo import JobAbstractRepository
from jobs.data.db_repo import JobDbRepository
from jobs.infrastructure.ssh_client import SSHClientInterface, SSHClient
from jobs.infrastructure.remote_command_executor import RemoteCommandExecutorInterface, RemoteCommandExecutor
from jobs.domain.use_cases.create_job_use_case import CreateJobUseCase
from jobs.domain.use_cases.get_job_use_case import GetJobUseCase
from jobs.domain.use_cases.list_jobs_use_case import ListJobsUseCase
from jobs.domain.use_cases.update_job_use_case import UpdateJobUseCase
from jobs.domain.use_cases.cancel_job_use_case import CancelJobUseCase
from jobs.domain.use_cases.delete_job_use_case import DeleteJobUseCase
from jobs.domain.use_cases.execute_remote_command_use_case import ExecuteRemoteCommandUseCase
from jobs.domain.use_cases.execute_remote_command_streaming_use_case import ExecuteRemoteCommandStreamingUseCase
from jobs.domain.use_cases.kill_remote_process_use_case import KillRemoteProcessUseCase


class JobContainer(containers.DeclarativeContainer):
    # Infrastructure
    ssh_client = providers.Dependency(
        instance_of=SSHClientInterface,
        default=SSHClient(),
    )
    remote_executor = providers.Dependency(
        instance_of=RemoteCommandExecutorInterface,
        default=RemoteCommandExecutor(),
    )

    # db repository
    db_repo = providers.Dependency(
        instance_of=JobAbstractRepository,
        default=JobDbRepository(),
    )

    # Use cases
    create_job_use_case = providers.Factory(CreateJobUseCase)
    get_job_use_case = providers.Factory(GetJobUseCase)
    list_jobs_use_case = providers.Factory(ListJobsUseCase)
    update_job_use_case = providers.Factory(UpdateJobUseCase)
    cancel_job_use_case = providers.Factory(CancelJobUseCase)
    delete_job_use_case = providers.Factory(DeleteJobUseCase)
    execute_remote_command_use_case = providers.Factory(ExecuteRemoteCommandUseCase)
    execute_remote_command_streaming_use_case = providers.Factory(ExecuteRemoteCommandStreamingUseCase)
    kill_remote_process_use_case = providers.Factory(KillRemoteProcessUseCase)
