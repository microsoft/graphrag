# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Collection of callbacks that can be used to monitor the workflow execution."""

from typing import Protocol

from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.logger.progress import Progress


class WorkflowCallbacks(Protocol):
    """
    A collection of callbacks that can be used to monitor the workflow execution.

    This base class is a "noop" implementation so that clients may implement just the callbacks they need.
    """

    def pipeline_start(self, names: list[str]) -> None:
        """Execute this callback to signal when the entire pipeline starts."""
        ...

    def pipeline_end(self, results: list[PipelineRunResult]) -> None:
        """Execute this callback to signal when the entire pipeline ends."""
        ...

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        ...

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        ...

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
        ...

    def error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Handle when an error occurs."""
        ...

    def warning(self, message: str, details: dict | None = None) -> None:
        """Handle when a warning occurs."""
        ...

    def log(self, message: str, details: dict | None = None) -> None:
        """Handle when a log message occurs."""
        ...
