# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Null Progress Reporter."""

from graphrag.logging.base import Progress, ProgressReporter


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
