# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A logger that emits updates from the indexing engine to the console."""

import logging
import sys


class ConsoleWorkflowLogger(logging.StreamHandler):
    """A logging handler that writes to console."""

    def __init__(self, level: int = logging.NOTSET):
        """Initialize the console handler."""
        super().__init__(sys.stdout)
        self.setLevel(level)

        # Set up a formatter for console output
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.setFormatter(formatter)

    def emit(self, record):
        """Emit a log record using the StreamHandler."""
        # For warning records, add color formatting if the message is just a warning
        if record.levelno == logging.WARNING and hasattr(record, "details"):
            # Apply warning color formatting similar to original
            formatted_msg = f"\033[93m{record.getMessage()}\033[00m"
            # Create a new record with the colored message
            colored_record = logging.LogRecord(
                record.name,
                record.levelno,
                record.pathname,
                record.lineno,
                formatted_msg,
                (),
                record.exc_info,
            )
            super().emit(colored_record)
        else:
            super().emit(record)
