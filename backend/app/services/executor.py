"""Execution engine for sandboxed Azure CLI command execution."""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import docker
from docker.models.containers import Container

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a single command execution."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: datetime
    completed_at: datetime


class ExecutionError(Exception):
    """Exception raised when execution fails."""

    pass


class Executor:
    """Sandboxed Azure CLI command executor."""

    def __init__(self):
        """Initialize executor with Docker client."""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    async def execute_commands(
        self,
        commands: list[str],
        azure_credentials: dict[str, str],
        timeout_seconds: int = settings.execution_timeout_seconds,
        output_callback: Optional[callable] = None,
    ) -> list[ExecutionResult]:
        """
        Execute Azure CLI commands in isolated Docker container.
        
        Args:
            commands: List of Azure CLI commands to execute
            azure_credentials: Azure service principal credentials
            timeout_seconds: Maximum execution time
            output_callback: Optional callback for streaming output
            
        Returns:
            List of execution results
            
        Raises:
            ExecutionError: If execution fails
        """
        container = None
        results = []

        try:
            # Create isolated Docker container
            container = self._create_container(azure_credentials)
            container.start()

            logger.info(f"Started execution container: {container.id[:12]}")

            # Execute commands sequentially
            for i, command in enumerate(commands):
                logger.info(f"Executing command {i+1}/{len(commands)}: {command}")

                started_at = datetime.utcnow()

                try:
                    # Execute command in container
                    exit_code, output = await self._exec_command_in_container(
                        container,
                        command,
                        timeout_seconds,
                        output_callback,
                    )

                    completed_at = datetime.utcnow()
                    duration = (completed_at - started_at).total_seconds()

                    # Parse stdout/stderr
                    stdout, stderr = self._parse_output(output)

                    result = ExecutionResult(
                        command=command,
                        exit_code=exit_code,
                        stdout=stdout,
                        stderr=stderr,
                        duration_seconds=duration,
                        started_at=started_at,
                        completed_at=completed_at,
                    )

                    results.append(result)

                    # Stop on error (unless continue_on_error is set)
                    if exit_code != 0:
                        logger.warning(f"Command failed with exit code {exit_code}")
                        break

                except asyncio.TimeoutError:
                    logger.error(f"Command timed out after {timeout_seconds}s")
                    raise ExecutionError(f"Command timed out: {command}")

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise ExecutionError(str(e))

        finally:
            # Clean up container
            if container:
                try:
                    container.stop(timeout=5)
                    container.remove()
                    logger.info(f"Cleaned up container: {container.id[:12]}")
                except Exception as e:
                    logger.error(f"Failed to clean up container: {e}")

        return results

    def _create_container(self, azure_credentials: dict[str, str]) -> Container:
        """
        Create isolated Docker container for execution.
        
        Args:
            azure_credentials: Azure service principal credentials
            
        Returns:
            Docker container (not started)
        """
        # Environment variables for Azure authentication
        environment = {
            "AZURE_TENANT_ID": azure_credentials["tenant_id"],
            "AZURE_CLIENT_ID": azure_credentials["client_id"],
            "AZURE_CLIENT_SECRET": azure_credentials["client_secret"],
            "AZURE_SUBSCRIPTION_ID": azure_credentials["subscription_id"],
        }

        # Create container with security constraints
        container = self.docker_client.containers.create(
            image=settings.docker_execution_image,
            command="sleep infinity",  # Keep container alive
            detach=True,
            environment=environment,
            network_mode="bridge",  # Isolated network
            mem_limit="512m",  # Memory limit
            cpu_quota=50000,  # 0.5 CPU
            security_opt=["no-new-privileges"],  # Security hardening
            read_only=False,  # Azure CLI needs to write to tmp
            tmpfs={"/tmp": "size=100m,mode=1777"},  # Writable tmp
            auto_remove=False,  # We'll remove manually
            user="1000:1000",  # Non-root user
        )

        return container

    async def _exec_command_in_container(
        self,
        container: Container,
        command: str,
        timeout_seconds: int,
        output_callback: Optional[callable] = None,
    ) -> tuple[int, bytes]:
        """
        Execute command inside container.
        
        Args:
            container: Docker container
            command: Command to execute
            timeout_seconds: Timeout in seconds
            output_callback: Optional callback for streaming output
            
        Returns:
            Tuple of (exit_code, output_bytes)
        """
        # Login to Azure using service principal
        login_command = "az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID"

        # Set default subscription
        subscription_command = "az account set --subscription $AZURE_SUBSCRIPTION_ID"

        # Full command with login
        full_command = f"bash -c '{login_command} && {subscription_command} && {command}'"

        # Execute in container
        exec_instance = container.exec_run(
            full_command,
            demux=True,  # Separate stdout/stderr
            stream=True,  # Stream output
        )

        # Collect output
        output = b""
        start_time = datetime.utcnow()

        for stdout_chunk, stderr_chunk in exec_instance.output:
            if (datetime.utcnow() - start_time).total_seconds() > timeout_seconds:
                raise asyncio.TimeoutError()

            if stdout_chunk:
                output += stdout_chunk
                if output_callback:
                    await output_callback(stdout_chunk.decode("utf-8", errors="replace"))

            if stderr_chunk:
                output += stderr_chunk
                if output_callback:
                    await output_callback(stderr_chunk.decode("utf-8", errors="replace"))

            # Small delay to prevent busy loop
            await asyncio.sleep(0.01)

        exit_code = exec_instance.exit_code

        return exit_code, output

    def _parse_output(self, output: bytes) -> tuple[str, str]:
        """
        Parse command output into stdout and stderr.
        
        Args:
            output: Raw output bytes
            
        Returns:
            Tuple of (stdout, stderr)
        """
        # Decode output
        decoded = output.decode("utf-8", errors="replace")

        # Simple heuristic: treat lines starting with "ERROR" as stderr
        stdout_lines = []
        stderr_lines = []

        for line in decoded.split("\n"):
            if line.startswith("ERROR") or line.startswith("WARNING"):
                stderr_lines.append(line)
            else:
                stdout_lines.append(line)

        return "\n".join(stdout_lines), "\n".join(stderr_lines)
