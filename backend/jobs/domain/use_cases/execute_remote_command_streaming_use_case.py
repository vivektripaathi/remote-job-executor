import logging
from dependency_injector.wiring import Provide

from jobs.infrastructure.remote_command_executor import RemoteCommandExecutorInterface

logger = logging.getLogger(__name__)


class ExecuteRemoteCommandStreamingUseCase:
    def __init__(
        self,
        remote_executor: RemoteCommandExecutorInterface = Provide["remote_executor"],
    ) -> None:
        self.remote_executor = remote_executor

    async def execute(self, job_id: str, command: str, timeout: int = 60) -> tuple[str, str]:
        logger.info(f"Executing remote command with streaming for job {job_id}: {command}")
        try:
            stdout, stderr = await self.remote_executor.execute_command_streaming(job_id, command, timeout)
            logger.info(f"Streaming command executed successfully for job {job_id}")
            return stdout, stderr
        except Exception as e:
            logger.error(f"Failed to execute streaming remote command for job {job_id}: {e}")
            raise
