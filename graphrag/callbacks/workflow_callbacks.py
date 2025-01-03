# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Collection of callbacks that can be used to monitor the workflow execution."""

from typing import Any, Protocol

from graphrag.logger.progress import Progress


class WorkflowCallbacks(Protocol):
    """
    A collection of callbacks that can be used to monitor the workflow execution.

    This base class is a "noop" implementation so that clients may implement just the callbacks they need.
    """

    def on_workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        ...

    def on_workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        ...

    def on_step_start(self, step_name: str) -> None:
        """Execute this callback every time a step starts."""
        ...

    def on_step_end(self, step_name: str, result: Any) -> None:
        """Execute this callback every time a step ends."""
        ...

    def on_step_progress(self, step_name: str, progress: Progress) -> None:
        """Handle when progress occurs."""
        ...

    def on_error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Handle when an error occurs."""
        ...

    def on_warning(self, message: str, details: dict | None = None) -> None:
        """Handle when a warning occurs."""
        ...

    def on_log(self, message: str, details: dict | None = None) -> None:
        """Handle when a log message occurs."""
        ...

    def on_measure(self, name: str, value: float, details: dict | None = None) -> None:
        """Handle when a measurement occurs."""
        ...
