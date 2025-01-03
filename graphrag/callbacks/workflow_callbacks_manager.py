# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the WorkflowCallbacks registry."""

from typing import Any

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.logger.progress import Progress


class WorkflowCallbacksManager(WorkflowCallbacks):
    """A registry of WorkflowCallbacks."""

    _callbacks: list[WorkflowCallbacks]

    def __init__(self):
        """Create a new instance of WorkflowCallbacksRegistry."""
        self._callbacks = []

    def register(self, callbacks: WorkflowCallbacks) -> None:
        """Register a new WorkflowCallbacks type."""
        self._callbacks.append(callbacks)

    def on_workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        for callback in self._callbacks:
            if hasattr(callback, "on_workflow_start"):
                callback.on_workflow_start(name, instance)

    def on_workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        for callback in self._callbacks:
            if hasattr(callback, "on_workflow_end"):
                callback.on_workflow_end(name, instance)

    def on_step_start(self, step_name: str) -> None:
        """Execute this callback every time a step starts."""
        for callback in self._callbacks:
            if hasattr(callback, "on_step_start"):
                callback.on_step_start(step_name)

    def on_step_end(self, step_name: str, result: Any) -> None:
        """Execute this callback every time a step ends."""
        for callback in self._callbacks:
            if hasattr(callback, "on_step_end"):
                callback.on_step_end(step_name, result)

    def on_step_progress(self, step_name: str, progress: Progress) -> None:
        """Handle when progress occurs."""
        for callback in self._callbacks:
            if hasattr(callback, "on_step_progress"):
                callback.on_step_progress(step_name, progress)

    def on_error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Handle when an error occurs."""
        for callback in self._callbacks:
            if hasattr(callback, "on_error"):
                callback.on_error(message, cause, stack, details)

    def on_warning(self, message: str, details: dict | None = None) -> None:
        """Handle when a warning occurs."""
        for callback in self._callbacks:
            if hasattr(callback, "on_warning"):
                callback.on_warning(message, details)

    def on_log(self, message: str, details: dict | None = None) -> None:
        """Handle when a log message occurs."""
        for callback in self._callbacks:
            if hasattr(callback, "on_log"):
                callback.on_log(message, details)

    def on_measure(self, name: str, value: float, details: dict | None = None) -> None:
        """Handle when a measurement occurs."""
        for callback in self._callbacks:
            if hasattr(callback, "on_measure"):
                callback.on_measure(name, value, details)
