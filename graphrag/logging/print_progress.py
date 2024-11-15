# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Print Progress Reporter."""

from graphrag.logging.base import Progress, ProgressReporter


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
