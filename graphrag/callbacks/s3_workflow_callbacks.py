# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A logger that emits updates from the indexing engine to an S3 bucket."""

import json
import logging
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any

from botocore.client import BaseClient
from botocore.exceptions import ClientError

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.utils.aws import create_s3_client

logger = logging.getLogger(__name__)


class LogType(Enum):
    """Enum for log entry types."""

    ERROR = auto()
    WARNING = auto()
    LOG = auto()


class S3WorkflowCallbacks(NoopWorkflowCallbacks):
    """
    A logger that writes workflow events to an S3 bucket.

    This class handles writing log messages, warnings, and errors to an s3 bucket.
    It manages log file rotation when the number of blocks exceeds the maximum limit.
    """

    # This will be lazily loaded
    __s3_client: BaseClient | None = None
    _bucket_name: str
    _prefix: str
    _encoding: str
    _log_file_prefix: str
    _num_blocks: int
    _max_block_count: int = 25_000  # 25k blocks per log file

    def __init__(
        self,
        bucket_name: str | None,
        base_dir: str = "",
        log_file_name: str = "",
        encoding: str = "utf-8",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str | None = None,
        endpoint_url: str | None = None,
    ):
        """
        Create a new instance of the S3WorkflowCallbacks class.

        Args:
            bucket_name: The name of the S3 bucket to write logs to.
            base_dir: Base directory path within the bucket; used as a prefix.
            log_file_name: Name of the log file to write to.
            encoding: Character encoding to use for the log file.
            aws_access_key_id: The AWS access key ID. If not provided, boto3's credential chain will be used.
            aws_secret_access_key: The AWS secret access key. If not provided, boto3's credential chain will be used.
            region_name: The AWS region name. If not provided, boto3's default region will be used.
            endpoint_url: The endpoint URL for the S3 API. If provided, this will be used instead of the default AWS S3 endpoint.
                          This is useful for connecting to S3-compatible storage services like MinIO.

        Raises
        ------
            ValueError: If not bucket name is provided.
        """
        if not bucket_name:
            msg = "No bucket name provided for S3 storage."
            raise ValueError(msg)

        self._bucket_name = bucket_name
        self._prefix = base_dir
        self._encoding = encoding

        # Store credentials for lazy initialization
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._region_name = region_name
        self._endpoint_url = endpoint_url

        if not log_file_name:
            log_file_name = _get_log_file_name()

        self._log_file_prefix = str(Path(self._prefix) / log_file_name)
        self._num_blocks = 0  # refresh block counter

    @property
    def _s3_client(self) -> BaseClient:
        """Lazy load the S3 client."""
        if self.__s3_client is None:
            self.__s3_client = create_s3_client(
                endpoint_url=self._endpoint_url,
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self._region_name,
            )

        return self.__s3_client

    def _write_log(self, log_entry: dict[str, Any]) -> None:
        """
        Write a log entry to the S3 bucket.

        Args:
            log_entry: Dictionary containing the log data.
        """
        # Create a new log file when block count hits close to 25k
        if self._num_blocks >= self._max_block_count:
            # Generate a new log file name with current timestamp
            new_log_file = _get_log_file_name()
            # Reset block counter
            self._num_blocks = 0
            # Update log file prefix but don't reinitialize the entire object
            self._log_file_prefix = str(Path(self._prefix) / new_log_file)
            logger.info(
                "Created new log file due to block count limit: %s", new_log_file
            )

        try:
            log_content = json.dumps(log_entry, indent=4, ensure_ascii=False) + "\n"
            # Use append-like behavior by using a unique key for each log entry
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S%f")
            log_key = f"{self._log_file_prefix}_{self._num_blocks}_{timestamp}"

            self._s3_client.put_object(
                Bucket=self._bucket_name,
                Key=log_key,
                Body=log_content.encode(self._encoding),
            )
            self._num_blocks += 1
            logger.debug(
                "Successfully wrote log entry to S3: %s",
                log_entry.get("type", "unknown"),
            )
        except ClientError:
            logger.exception("Failed to write log to S3 bucket %s", self._bucket_name)
            # Don't re-raise to maintain the no-op behavior pattern

    def _log_message(
        self,
        log_type: LogType,
        message: str,
        log_level: int,
        details: dict | None = None,
        cause: BaseException | None = None,
        stack: str | None = None,
    ) -> None:
        """
        Log messages with a consistent formatting.

        Args:
            log_type: Type of log entry (error, warning, log)
            message: The message to log
            log_level: Python logging level to use
            details: Additional details to include
            cause: Exception that caused an error (for error logs)
            stack: Stack trace (for error logs)
        """
        # Log to python logger
        if cause and log_type == LogType.ERROR:
            logger.log(
                log_level,
                "%s - %s",
                message,
                str(cause) if cause else "No cause specified",
            )
        else:
            logger.log(log_level, message)

        # Create a log entry
        log_entry = {
            "type": log_type.name.lower(),
            "data": message,
            "details": details,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

        # Add error-specific fields if applicable
        if log_type == LogType.ERROR:
            log_entry["cause"] = str(cause) if cause else None
            log_entry["stack"] = stack

        self._write_log(log_entry)

    def error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """
        Handle when an error occurs.

        Args:
            message: The error message to log
            cause: The exception that caused the error, if any
            stack: The stack trace as a string, if available
            details: Additional details about the error as a dictionary, if any
        """
        self._log_message(
            log_type=LogType.ERROR,
            message=message,
            log_level=logging.ERROR,
            details=details,
            cause=cause,
            stack=stack,
        )

    def warning(self, message: str, details: dict | None = None) -> None:
        """
        Handle when a warning occurs.

        Args:
            message: The warning message to log
            details: Additional details about the warning as a dictionary, if any
        """
        self._log_message(
            log_type=LogType.WARNING,
            message=message,
            log_level=logging.WARNING,
            details=details,
        )

    def log(self, message: str, details: dict | None = None) -> None:
        """
        Handle when a log message occurs.

        Args:
            message: The log message to record
            details: Additional details about the log entry as a dictionary, if any
        """
        self._log_message(
            log_type=LogType.LOG,
            message=message,
            log_level=logging.INFO,
            details=details,
        )


def _get_log_file_name() -> str:
    """Get a default log file name used for this module."""
    return f"report/{datetime.now(tz=timezone.utc).strftime('%Y-%m-%d-%H:%M:%S:%f')}.logs.json"
