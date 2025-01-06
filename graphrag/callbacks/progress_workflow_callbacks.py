# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A workflow callback manager that emits updates."""

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.logger.base import ProgressLogger
from graphrag.logger.progress import Progress


class ProgressWorkflowCallbacks(NoopWorkflowCallbacks):
    """A callbackmanager that delegates to a ProgressLogger."""

    _root_progress: ProgressLogger
    _progress_stack: list[ProgressLogger]

    def __init__(self, progress: ProgressLogger) -> None:
        """Create a new ProgressWorkflowCallbacks."""
        self._progress = progress
        self._progress_stack = [progress]

    def _pop(self) -> None:
        self._progress_stack.pop()

    def _push(self, name: str) -> None:
        self._progress_stack.append(self._latest.child(name))

    @property
    def _latest(self) -> ProgressLogger:
        return self._progress_stack[-1]

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        self._push(name)

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        self._pop()

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
        self._latest(progress)
