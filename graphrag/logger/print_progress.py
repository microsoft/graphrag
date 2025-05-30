# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Print Progress Logger."""

import logging

from graphrag.logger.base import Progress, ProgressLogger
from graphrag.logger.standard_logging import get_logger


class PrintProgressLogger(ProgressLogger):
    """A progress logger that prints progress to stdout."""

    prefix: str
    _logger: logging.Logger

    def __init__(self, prefix: str):
        """Create a new progress logger."""
        self.prefix = prefix
        self._logger = get_logger("graphrag.progress")
        self._logger.info(f"{self.prefix}")

    def __call__(self, update: Progress) -> None:
        """Update progress."""
        self._logger.debug(".", extra={"progress": True})
        # Keep the legacy behavior of printing dots for progress
        print(".", end="")  # noqa T201

    def dispose(self) -> None:
        """Dispose of the progress logger."""
        pass

    def child(self, prefix: str, transient: bool = True) -> ProgressLogger:
        """Create a child progress bar."""
        return PrintProgressLogger(prefix)

    def stop(self) -> None:
        """Stop the progress logger."""
        pass

    def force_refresh(self) -> None:
        """Force a refresh."""
        pass

    def error(self, message: str) -> None:
        """Log an error."""
        self._logger.error(f"{self.prefix}{message}")

    def warning(self, message: str) -> None:
        """Log a warning."""
        self._logger.warning(f"{self.prefix}{message}")

    def info(self, message: str) -> None:
        """Log information."""
        self._logger.info(f"{self.prefix}{message}")

    def success(self, message: str) -> None:
        """Log success."""
        self._logger.info(f"{self.prefix}SUCCESS: {message}")
