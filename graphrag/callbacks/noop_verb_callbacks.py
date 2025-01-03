# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Defines the interface for verb callbacks."""

from graphrag.callbacks.verb_callbacks import VerbCallbacks
from graphrag.logger.progress import Progress


class NoopVerbCallbacks(VerbCallbacks):
    """A noop implementation of the verb callbacks."""

    def __init__(self) -> None:
        pass

    def progress(self, progress: Progress) -> None:
        """Report a progress update from the verb execution"."""

    def error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Report a error from the verb execution."""

    def warning(self, message: str, details: dict | None = None) -> None:
        """Report a warning from verb execution."""

    def log(self, message: str, details: dict | None = None) -> None:
        """Report an informational message from the verb execution."""

    def measure(self, name: str, value: float) -> None:
        """Report a telemetry measurement from the verb execution."""
