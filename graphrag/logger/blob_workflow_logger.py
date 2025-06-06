# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A logger that emits updates from the indexing engine to a blob in Azure Storage."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class BlobWorkflowLogger(logging.Handler):
    """A logging handler that writes to a blob storage account."""

    _blob_service_client: BlobServiceClient
    _container_name: str
    _max_block_count: int = 25000  # 25k blocks per blob

    def __init__(
        self,
        connection_string: str | None,
        container_name: str | None,
        blob_name: str = "",
        base_dir: str | None = None,
        storage_account_blob_url: str | None = None,
        level: int = logging.NOTSET,
    ):
        """Create a new instance of the BlobWorkflowLogger class."""
        super().__init__(level)

        if container_name is None:
            msg = "No container name provided for blob storage."
            raise ValueError(msg)
        if connection_string is None and storage_account_blob_url is None:
            msg = "No storage account blob url provided for blob storage."
            raise ValueError(msg)

        self._connection_string = connection_string
        self._storage_account_blob_url = storage_account_blob_url

        if self._connection_string:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                self._connection_string
            )
        else:
            if storage_account_blob_url is None:
                msg = "Either connection_string or storage_account_blob_url must be provided."
                raise ValueError(msg)

            self._blob_service_client = BlobServiceClient(
                storage_account_blob_url,
                credential=DefaultAzureCredential(),
            )

        if blob_name == "":
            blob_name = f"report/{datetime.now(tz=timezone.utc).strftime('%Y-%m-%d-%H:%M:%S:%f')}.logs.json"

        self._blob_name = str(Path(base_dir or "") / blob_name)
        self._container_name = container_name
        self._blob_client = self._blob_service_client.get_blob_client(
            self._container_name, self._blob_name
        )
        if not self._blob_client.exists():
            self._blob_client.create_append_blob()

        self._num_blocks = 0  # refresh block counter

    def emit(self, record) -> None:
        """Emit a log record to blob storage."""
        try:
            # Create JSON structure based on record
            log_data = {
                "type": self._get_log_type(record.levelno),
                "data": record.getMessage(),
            }

            # Add additional fields if they exist
            if hasattr(record, "details") and record.details:  # type: ignore[reportAttributeAccessIssue]
                log_data["details"] = record.details  # type: ignore[reportAttributeAccessIssue]
            if record.exc_info and record.exc_info[1]:
                log_data["cause"] = str(record.exc_info[1])
            if hasattr(record, "stack") and record.stack:  # type: ignore[reportAttributeAccessIssue]
                log_data["stack"] = record.stack  # type: ignore[reportAttributeAccessIssue]

            self._write_log(log_data)
        except (OSError, ValueError):
            self.handleError(record)

    def _get_log_type(self, level: int) -> str:
        """Get log type string based on log level."""
        if level >= logging.ERROR:
            return "error"
        if level >= logging.WARNING:
            return "warning"
        return "log"

    def _write_log(self, log: dict[str, Any]):
        """Write log data to blob storage."""
        # create a new file when block count hits close 25k
        if (
            self._num_blocks >= self._max_block_count
        ):  # Check if block count exceeds 25k
            self.__init__(
                self._connection_string,
                self._container_name,
                storage_account_blob_url=self._storage_account_blob_url,
            )

        blob_client = self._blob_service_client.get_blob_client(
            self._container_name, self._blob_name
        )
        blob_client.append_block(json.dumps(log, indent=4, ensure_ascii=False) + "\n")

        # update the blob's block count
        self._num_blocks += 1
