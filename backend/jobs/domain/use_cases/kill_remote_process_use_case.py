import logging
from dependency_injector.wiring import Provide

from jobs.infrastructure.remote_command_executor import RemoteCommandExecutorInterface

logger = logging.getLogger(__name__)


class KillRemoteProcessUseCase:
    def __init__(
        self,
        remote_executor: RemoteCommandExecutorInterface = Provide["remote_executor"],
    ) -> None:
        self.remote_executor = remote_executor

    def execute(self, pid: str) -> None:
        logger.info(f"Killing remote process with PID: {pid}")
        try:
            self.remote_executor.kill_process(pid)
            logger.info(f"Process {pid} killed successfully")
        except Exception as e:
            logger.error(f"Failed to kill remote process {pid}: {e}")
            raise
