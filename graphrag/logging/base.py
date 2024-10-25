# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for logging and progress reporting."""

from abc import ABC, abstractmethod
from typing import Any

from datashaper.progress.types import Progress


class StatusLogger(ABC):
    """Provides a way to report status updates from the pipeline."""

    @abstractmethod
    def error(self, message: str, details: dict[str, Any] | None = None):
        """Report an error."""

    @abstractmethod
    def warning(self, message: str, details: dict[str, Any] | None = None):
        """Report a warning."""

    @abstractmethod
    def log(self, message: str, details: dict[str, Any] | None = None):
        """Report a log."""


class ProgressReporter(ABC):
    """
    Abstract base class for progress reporters.

    This is used to report workflow processing progress via mechanisms like progress-bars.
    """

    @abstractmethod
    def __call__(self, update: Progress):
        """Update progress."""

    @abstractmethod
    def dispose(self):
        """Dispose of the progress reporter."""

    @abstractmethod
    def child(self, prefix: str, transient=True) -> "ProgressReporter":
        """Create a child progress bar."""

    @abstractmethod
    def force_refresh(self) -> None:
        """Force a refresh."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the progress reporter."""

    @abstractmethod
    def error(self, message: str) -> None:
        """Report an error."""

    @abstractmethod
    def warning(self, message: str) -> None:
        """Report a warning."""

    @abstractmethod
    def info(self, message: str) -> None:
        """Report information."""

    @abstractmethod
    def success(self, message: str) -> None:
        """Report success."""
