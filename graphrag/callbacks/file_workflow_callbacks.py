# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A logger that emits updates from the indexing engine to a local file."""

import json
import logging
from pathlib import Path

from graphrag.callbacks.workflow_handler_base import WorkflowHandlerBase


class WorkflowJSONFileHandler(logging.FileHandler):
    """A FileHandler that formats log records as JSON for workflow callbacks."""

    def emit(self, record):
        """Emit a log record as JSON."""
        try:
            # Create JSON structure based on record type
            log_data = {
                "type": self._get_log_type(record.levelno),
                "data": record.getMessage(),
            }

            # Add additional fields if they exist
            if hasattr(record, "details") and record.details:  # type: ignore[reportAttributeAccessIssue]
                log_data["details"] = record.details  # type: ignore[reportAttributeAccessIssue]
            if record.exc_info and record.exc_info[1]:
                log_data["source"] = str(record.exc_info[1])
            if hasattr(record, "stack") and record.stack:  # type: ignore[reportAttributeAccessIssue]
                log_data["stack"] = record.stack  # type: ignore[reportAttributeAccessIssue]

            # Write JSON to file
            json_str = json.dumps(log_data, indent=4, ensure_ascii=False) + "\n"

            if self.stream is None:
                self.stream = self._open()
            self.stream.write(json_str)
            self.flush()
        except (OSError, ValueError):
            self.handleError(record)

    def _get_log_type(self, level: int) -> str:
        """Get log type string based on log level."""
        if level >= logging.ERROR:
            return "error"
        if level >= logging.WARNING:
            return "warning"
        return "log"


class FileWorkflowCallbacks(WorkflowHandlerBase):
    """A workflow callback handler that writes to a local file using FileHandler."""

    def __init__(self, directory: str, level: int = logging.NOTSET):
        """Create a new file-based workflow handler."""
        super().__init__(level)

        # Ensure directory exists
        Path(directory).mkdir(parents=True, exist_ok=True)

        # Create the JSON file handler
        log_file_path = Path(directory) / "logs.json"
        self._file_handler = WorkflowJSONFileHandler(str(log_file_path), mode="a")

        # Also create a regular logger for backwards compatibility
        self._logger = logging.getLogger(__name__)

    def emit(self, record):
        """Emit a log record using the underlying FileHandler."""
        # Emit to the JSON file
        self._file_handler.emit(record)

        # Also emit to regular logger for backwards compatibility
        if record.levelno >= logging.WARNING:
            self._logger.log(record.levelno, record.getMessage())

    def close(self):
        """Close the file handler."""
        super().close()
        self._file_handler.close()
