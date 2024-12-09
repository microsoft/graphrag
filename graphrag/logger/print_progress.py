# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Print Progress Logger."""

from graphrag.logger.base import Progress, ProgressLogger


class PrintProgressLogger(ProgressLogger):
    """A progress logger that prints progress to stdout."""

    prefix: str

    def __init__(self, prefix: str):
        """Create a new progress logger."""
        self.prefix = prefix
        print(f"\n{self.prefix}", end="")  # noqa T201

    def __call__(self, update: Progress) -> None:
        """Update progress."""
        print(".", end="")  # noqa T201

    def dispose(self) -> None:
        """Dispose of the progress logger."""

    def child(self, prefix: str, transient: bool = True) -> ProgressLogger:
        """Create a child progress bar."""
        return PrintProgressLogger(prefix)

    def stop(self) -> None:
        """Stop the progress logger."""

    def force_refresh(self) -> None:
        """Force a refresh."""

    def error(self, message: str) -> None:
        """Log an error."""
        print(f"\n{self.prefix}ERROR: {message}")  # noqa T201

    def warning(self, message: str) -> None:
        """Log a warning."""
        print(f"\n{self.prefix}WARNING: {message}")  # noqa T201

    def info(self, message: str) -> None:
        """Log information."""
        print(f"\n{self.prefix}INFO: {message}")  # noqa T201

    def success(self, message: str) -> None:
        """Log success."""
        print(f"\n{self.prefix}SUCCESS: {message}")  # noqa T201
