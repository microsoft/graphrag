# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A no-op implementation of WorkflowCallbacks."""

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.logger.progress import Progress


class NoopWorkflowCallbacks(WorkflowCallbacks):
    """A no-op implementation of WorkflowCallbacks."""

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""

    def error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Handle when an error occurs."""

    def warning(self, message: str, details: dict | None = None) -> None:
        """Handle when a warning occurs."""

    def log(self, message: str, details: dict | None = None) -> None:
        """Handle when a log message occurs."""
