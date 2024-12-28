# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for logging and progress reporting."""

from abc import ABC, abstractmethod
from typing import Any

from graphrag.logger.progress import Progress


class StatusLogger(ABC):
    """Provides a way to log status updates from the pipeline."""

    @abstractmethod
    def error(self, message: str, details: dict[str, Any] | None = None):
        """Log an error."""

    @abstractmethod
    def warning(self, message: str, details: dict[str, Any] | None = None):
        """Log a warning."""

    @abstractmethod
    def log(self, message: str, details: dict[str, Any] | None = None):
        """Report a log."""


class ProgressLogger(ABC):
    """
    Abstract base class for progress loggers.

    This is used to report workflow processing progress via mechanisms like progress-bars.
    """

    @abstractmethod
    def __call__(self, update: Progress):
        """Update progress."""

    @abstractmethod
    def dispose(self):
        """Dispose of the progress logger."""

    @abstractmethod
    def child(self, prefix: str, transient=True) -> "ProgressLogger":
        """Create a child progress bar."""

    @abstractmethod
    def force_refresh(self) -> None:
        """Force a refresh."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the progress logger."""

    @abstractmethod
    def error(self, message: str) -> None:
        """Log an error."""

    @abstractmethod
    def warning(self, message: str) -> None:
        """Log a warning."""

    @abstractmethod
    def info(self, message: str) -> None:
        """Log information."""

    @abstractmethod
    def success(self, message: str) -> None:
        """Log success."""
