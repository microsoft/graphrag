# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Null Progress Reporter."""

import logging

from graphrag.logger.base import Progress, ProgressLogger
from graphrag.logger.standard_logging import get_logger


class NullProgressLogger(ProgressLogger):
    """A progress logger that does nothing."""
    
    _logger: logging.Logger

    def __init__(self):
        """Initialize the null progress logger."""
        self._logger = get_logger("graphrag.progress.null")
    
    def __call__(self, update: Progress) -> None:
        """Update progress."""
        # We don't log anything for progress updates in the null logger
        pass

    def dispose(self) -> None:
        """Dispose of the progress logger."""
        pass

    def child(self, prefix: str, transient: bool = True) -> ProgressLogger:
        """Create a child progress bar."""
        return self

    def force_refresh(self) -> None:
        """Force a refresh."""
        pass

    def stop(self) -> None:
        """Stop the progress logger."""
        pass

    def error(self, message: str) -> None:
        """Log an error."""
        self._logger.error(message)

    def warning(self, message: str) -> None:
        """Log a warning."""
        self._logger.warning(message)

    def info(self, message: str) -> None:
        """Log information."""
        self._logger.info(message)

    def success(self, message: str) -> None:
        """Log success."""
        self._logger.info(f"SUCCESS: {message}")
