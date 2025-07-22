# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the WorkflowCallbacks registry."""

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
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

    def pipeline_start(self, names: list[str]) -> None:
        """Execute this callback when a the entire pipeline starts."""
        for callback in self._callbacks:
            if hasattr(callback, "pipeline_start"):
                callback.pipeline_start(names)

    def pipeline_end(self, results: list[PipelineRunResult]) -> None:
        """Execute this callback when the entire pipeline ends."""
        for callback in self._callbacks:
            if hasattr(callback, "pipeline_end"):
                callback.pipeline_end(results)

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        for callback in self._callbacks:
            if hasattr(callback, "workflow_start"):
                callback.workflow_start(name, instance)

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        for callback in self._callbacks:
            if hasattr(callback, "workflow_end"):
                callback.workflow_end(name, instance)

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
        for callback in self._callbacks:
            if hasattr(callback, "progress"):
                callback.progress(progress)
