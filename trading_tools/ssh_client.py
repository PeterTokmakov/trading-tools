#!/usr/bin/env python3
# hash: 8e4f2a

"""
SSH Client module for trading tools.
Provides a unified SSH connection interface for all trading tools.
"""

import paramiko
from pathlib import Path
from typing import Optional, Tuple


class SSHClient:
    """Unified SSH client for trading tools."""
    
    def __init__(self, settings_path: Optional[Path] = None):
        """
        Initialize SSH client.
        
        Args:
            settings_path: Path to settings JSON file with SSH credentials
        """
        self.ssh_client = None
        self.sftp_client = None
        self.settings_path = settings_path
        self.settings = None
        
        if settings_path and settings_path.exists():
            self.load_settings()
    
    def load_settings(self) -> dict:
        """Load SSH settings from JSON file."""
        if not self.settings_path:
            raise ValueError("Settings path not provided")
        
        import json
        
        with open(self.settings_path, 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        return self.settings
    
    def connect(self, settings: Optional[dict] = None) -> None:
        """
        Connect to remote server via SSH.
        
        Args:
            settings: Optional settings dict (overrides loaded settings)
        """
        if settings:
            self.settings = settings
        elif not self.settings:
            self.load_settings()
        
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load SSH key
        key_path = self.settings["SSH_KEY_PATH"]
        private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
        
        self.ssh_client.connect(
            hostname=self.settings["REMOTE_HOST"],
            username=self.settings["SSH_USERNAME"],
            pkey=private_key
        )
        
        self.sftp_client = self.ssh_client.open_sftp()
    
    def execute_command(self, command: str, timeout: int = 300) -> Tuple[str, str, int]:
        """
        Execute command on remote server.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if not self.ssh_client:
            raise RuntimeError("Not connected to server")
        
        stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
        
        stdout_str = stdout.read().decode('utf-8')
        stderr_str = stderr.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()
        
        return stdout_str, stderr_str, exit_code
    
    def upload_file(self, local_path: str, remote_path: str) -> None:
        """
        Upload file to remote server.
        
        Args:
            local_path: Local file path
            remote_path: Remote file path
        """
        if not self.sftp_client:
            raise RuntimeError("Not connected to server")
        
        self.sftp_client.put(local_path, remote_path)
    
    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download file from remote server.
        
        Args:
            remote_path: Remote file path
            local_path: Local file path
        """
        if not self.sftp_client:
            raise RuntimeError("Not connected to server")
        
        self.sftp_client.get(remote_path, local_path)
    
    def list_directory(self, remote_path: str) -> list:
        """
        List directory contents on remote server.
        
        Args:
            remote_path: Remote directory path
            
        Returns:
            List of file/directory names
        """
        if not self.sftp_client:
            raise RuntimeError("Not connected to server")
        
        return self.sftp_client.listdir(remote_path)
    
    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists on remote server.
        
        Args:
            remote_path: Remote file path
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.sftp_client:
            raise RuntimeError("Not connected to server")
        
        try:
            self.sftp_client.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
    
    def close(self) -> None:
        """Close SSH connection."""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
        
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
