# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Standard Progress Logger using Python's built-in logging module."""

import logging

from graphrag.logger.base import Progress, ProgressLogger
from graphrag.logger.standard_logging import get_logger


class StandardProgressLogger(ProgressLogger):
    """A progress logger that uses Python's standard logging module."""

    _logger: logging.Logger
    _prefix: str

    def __init__(self, prefix: str = ""):
        """Initialize the standard progress logger.

        Parameters
        ----------
        prefix : str
            A prefix to add to all log messages
        """
        self._prefix = prefix
        self._logger = get_logger("graphrag.progress")
        if prefix:
            self._logger.info("%s", self._prefix)

    def __call__(self, update: Progress) -> None:
        """Update progress.

        Note: This logs progress information but does not show visual progress bars.
        """
        description = f" - {update.description}" if update.description else ""

        if update.completed_items is not None and update.total_items is not None:
            progress_msg = f"{self._prefix}Progress{description}: {update.completed_items}/{update.total_items}"
        elif update.percent is not None:
            progress_msg = f"{self._prefix}Progress{description}: {update.percent:.1%}"
        else:
            progress_msg = f"{self._prefix}Progress{description}"

        self._logger.debug(progress_msg)

    def dispose(self) -> None:
        """Dispose of the progress logger."""

    def child(self, prefix: str, transient: bool = True) -> ProgressLogger:
        """Create a child progress logger."""
        child_prefix = f"{self._prefix}{prefix}"
        return StandardProgressLogger(child_prefix)

    def force_refresh(self) -> None:
        """Force a refresh."""

    def stop(self) -> None:
        """Stop the progress logger."""
        if self._prefix:
            self._logger.info("%s completed", self._prefix)

    def error(self, message: str) -> None:
        """Log an error."""
        self._logger.error("%s%s", self._prefix, message)

    def warning(self, message: str) -> None:
        """Log a warning."""
        self._logger.warning("%s%s", self._prefix, message)

    def info(self, message: str) -> None:
        """Log information."""
        self._logger.info("%s%s", self._prefix, message)

    def success(self, message: str) -> None:
        """Log success."""
        self._logger.info("%sSUCCESS: %s", self._prefix, message)
