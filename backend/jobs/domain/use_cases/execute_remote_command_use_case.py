import logging
from dependency_injector.wiring import Provide

from jobs.infrastructure.remote_command_executor import RemoteCommandExecutorInterface

logger = logging.getLogger(__name__)


class ExecuteRemoteCommandUseCase:
    def __init__(
        self,
        remote_executor: RemoteCommandExecutorInterface = Provide["remote_executor"],
    ) -> None:
        self.remote_executor = remote_executor

    def execute(self, command: str, timeout: int = 60) -> tuple[str, str]:
        logger.info(f"Executing remote command: {command}")
        try:
            stdout, stderr = self.remote_executor.execute_command_sync(command, timeout)
            logger.info(f"Command executed successfully")
            return stdout, stderr
        except Exception as e:
            logger.error(f"Failed to execute remote command: {e}")
            raise
