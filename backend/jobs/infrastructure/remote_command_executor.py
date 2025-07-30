import asyncio
from abc import ABC, abstractmethod
from channels.layers import get_channel_layer

from jobs.infrastructure.ssh_client import SSHClientInterface


class RemoteCommandExecutorInterface(ABC):
    @abstractmethod
    def execute_command_sync(self, command: str, timeout: int = 60):
        pass

    @abstractmethod
    async def execute_command_streaming(self, job_id: str, command: str, timeout: int = 60):
        pass

    @abstractmethod
    def kill_process(self, pid: str):
        pass


class RemoteCommandExecutor(RemoteCommandExecutorInterface):
    def __init__(self, ssh_client: SSHClientInterface = None):
        from jobs.infrastructure.ssh_client import SSHClient
        self.ssh_client = ssh_client or SSHClient()

    def execute_command_sync(self, command: str, timeout: int = 60):
        ssh = self.ssh_client.get_connection()
        try:
            _, stdout, stderr = ssh.exec_command(command, timeout=timeout)
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output, error
        finally:
            self.ssh_client.close_connection(ssh)

    async def execute_command_streaming(self, job_id: str, command: str, timeout: int = 60):
        ssh = self.ssh_client.get_connection()
        
        try:
            channel = ssh.get_transport().open_session()
            channel.exec_command(command)

            channel_layer = get_channel_layer()

            stdout_buffer = ""
            stderr_buffer = ""
            
            start_time = asyncio.get_event_loop().time()

            while True:
                # Check for timeout
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > timeout:
                    # Send timeout message to WebSocket
                    await channel_layer.group_send(
                        f"job_logs_{job_id}",
                        {
                            "type": "send_log",
                            "log": f"\n⏰ Command timed out after {timeout} seconds\n",
                        },
                    )
                    channel.close()
                    raise TimeoutError(f"Command timed out after {timeout} seconds")
                    
                if channel.recv_ready():
                    data = channel.recv(1024).decode()
                    stdout_buffer += data
                    await channel_layer.group_send(
                        f"job_logs_{job_id}",
                        {
                            "type": "send_log",
                            "log": data,
                        },
                    )
                if channel.recv_stderr_ready():
                    data = channel.recv_stderr(1024).decode()
                    stderr_buffer += data
                    await channel_layer.group_send(
                        f"job_logs_{job_id}",
                        {
                            "type": "send_log",
                            "log": data,
                        },
                    )
                if channel.exit_status_ready():
                    break
                await asyncio.sleep(0.1)

            return stdout_buffer, stderr_buffer
        finally:
            self.ssh_client.close_connection(ssh)

    def kill_process(self, pid: str):
        ssh = self.ssh_client.get_connection()
        try:
            ssh.exec_command(f"kill -9 {pid}")
        finally:
            self.ssh_client.close_connection(ssh)
