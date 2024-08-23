# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Types for status reporting."""

from abc import ABC, abstractmethod

from datashaper import Progress


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


class NullProgressReporter(ProgressReporter):
    """A progress reporter that does nothing."""

    def __call__(self, update: Progress) -> None:
        """Update progress."""

    def dispose(self) -> None:
        """Dispose of the progress reporter."""

    def child(self, prefix: str, transient: bool = True) -> ProgressReporter:
        """Create a child progress bar."""
        return self

    def force_refresh(self) -> None:
        """Force a refresh."""

    def stop(self) -> None:
        """Stop the progress reporter."""

    def error(self, message: str) -> None:
        """Report an error."""

    def warning(self, message: str) -> None:
        """Report a warning."""

    def info(self, message: str) -> None:
        """Report information."""

    def success(self, message: str) -> None:
        """Report success."""


class PrintProgressReporter(ProgressReporter):
    """A progress reporter that does nothing."""

    prefix: str

    def __init__(self, prefix: str):
        """Create a new progress reporter."""
        self.prefix = prefix
        print(f"\n{self.prefix}", end="")  # noqa T201

    def __call__(self, update: Progress) -> None:
        """Update progress."""
        print(".", end="")  # noqa T201

    def dispose(self) -> None:
        """Dispose of the progress reporter."""

    def child(self, prefix: str, transient: bool = True) -> "ProgressReporter":
        """Create a child progress bar."""
        return PrintProgressReporter(prefix)

    def stop(self) -> None:
        """Stop the progress reporter."""

    def force_refresh(self) -> None:
        """Force a refresh."""

    def error(self, message: str) -> None:
        """Report an error."""
        print(f"\n{self.prefix}ERROR: {message}")  # noqa T201

    def warning(self, message: str) -> None:
        """Report a warning."""
        print(f"\n{self.prefix}WARNING: {message}")  # noqa T201

    def info(self, message: str) -> None:
        """Report information."""
        print(f"\n{self.prefix}INFO: {message}")  # noqa T201

    def success(self, message: str) -> None:
        """Report success."""
        print(f"\n{self.prefix}SUCCESS: {message}")  # noqa T201
