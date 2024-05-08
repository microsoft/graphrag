# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A workflow callback manager that emits updates to a ProgressReporter."""

from typing import Any

from datashaper import ExecutionNode, NoopWorkflowCallbacks, Progress, TableContainer

from graphrag.index.progress import ProgressReporter


class ProgressWorkflowCallbacks(NoopWorkflowCallbacks):
    """A callbackmanager that delegates to a ProgressReporter."""

    _root_progress: ProgressReporter
    _progress_stack: list[ProgressReporter]

    def __init__(self, progress: ProgressReporter) -> None:
        """Create a new ProgressWorkflowCallbacks."""
        self._progress = progress
        self._progress_stack = [progress]

    def _pop(self) -> None:
        self._progress_stack.pop()

    def _push(self, name: str) -> None:
        self._progress_stack.append(self._latest.child(name))

    @property
    def _latest(self) -> ProgressReporter:
        return self._progress_stack[-1]

    def on_workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        self._push(name)

    def on_workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        self._pop()

    def on_step_start(self, node: ExecutionNode, inputs: dict[str, Any]) -> None:
        """Execute this callback every time a step starts."""
        verb_id_str = f" ({node.node_id})" if node.has_explicit_id else ""
        self._push(f"Verb {node.verb.name}{verb_id_str}")
        self._latest(Progress(percent=0))

    def on_step_end(self, node: ExecutionNode, result: TableContainer | None) -> None:
        """Execute this callback every time a step ends."""
        self._pop()

    def on_step_progress(self, node: ExecutionNode, progress: Progress) -> None:
        """Handle when progress occurs."""
        self._latest(progress)
