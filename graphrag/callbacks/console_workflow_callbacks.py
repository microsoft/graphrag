# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A logger that emits updates from the indexing engine to the console."""

import logging
import sys

from graphrag.callbacks.workflow_handler_base import WorkflowHandlerBase


class ConsoleWorkflowCallbacks(WorkflowHandlerBase):
    """A workflow callback handler that writes to console using StreamHandler."""

    def __init__(self, level: int = logging.NOTSET):
        """Initialize the console handler."""
        super().__init__(level)
        # Use a StreamHandler for actual console output
        self._stream_handler = logging.StreamHandler(sys.stdout)
        
        # Set up a formatter for console output
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._stream_handler.setFormatter(formatter)

    def emit(self, record):
        """Emit a log record using the underlying StreamHandler."""
        # For warning records, add color formatting if the message is just a warning
        if record.levelno == logging.WARNING and hasattr(record, 'details'):
            # Apply warning color formatting similar to original
            formatted_msg = f"\033[93m{record.getMessage()}\033[00m"
            # Create a new record with the colored message
            colored_record = logging.LogRecord(
                record.name, record.levelno, record.pathname, record.lineno,
                formatted_msg, (), record.exc_info
            )
            self._stream_handler.emit(colored_record)
        else:
            self._stream_handler.emit(record)
