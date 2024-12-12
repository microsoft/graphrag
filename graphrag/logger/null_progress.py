# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Null Progress Reporter."""

from graphrag.logger.base import Progress, ProgressLogger


class NullProgressLogger(ProgressLogger):
    """A progress logger that does nothing."""

    def __call__(self, update: Progress) -> None:
        """Update progress."""

    def dispose(self) -> None:
        """Dispose of the progress logger."""

    def child(self, prefix: str, transient: bool = True) -> ProgressLogger:
        """Create a child progress bar."""
        return self

    def force_refresh(self) -> None:
        """Force a refresh."""

    def stop(self) -> None:
        """Stop the progress logger."""

    def error(self, message: str) -> None:
        """Log an error."""

    def warning(self, message: str) -> None:
        """Log a warning."""

    def info(self, message: str) -> None:
        """Log information."""

    def success(self, message: str) -> None:
        """Log success."""
