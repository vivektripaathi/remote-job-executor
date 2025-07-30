import os
import paramiko
from abc import ABC, abstractmethod


class SSHClientInterface(ABC):
    @abstractmethod
    def get_connection(self):
        pass

    @abstractmethod
    def close_connection(self, connection):
        pass

# TODO: Implement a more robust SSH client to support different systems and configurations
# Currently, this is a basic implementation for EC2 connections using Paramiko.
class SSHClient(SSHClientInterface):
    def get_connection(self):
        hostname = os.environ["EC2_HOST"]
        username = os.environ["EC2_USERNAME"]
        key_path = os.environ["EC2_KEY_PATH"]

        key = paramiko.RSAKey.from_private_key_file(key_path)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, pkey=key, timeout=10)

        return ssh

    def close_connection(self, connection):
        connection.close()
