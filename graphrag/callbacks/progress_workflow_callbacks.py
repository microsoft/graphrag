# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A workflow callback manager that emits updates."""

import logging

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.logger.progress import Progress


class ProgressWorkflowCallbacks(NoopWorkflowCallbacks):
    """A callback manager that delegates to a standard Logger."""

    _logger: logging.Logger
    _workflow_stack: list[str]

    def __init__(self, logger: logging.Logger) -> None:
        """Create a new ProgressWorkflowCallbacks."""
        self._logger = logger
        self._workflow_stack = []

    def _get_context(self) -> str:
        """Get the current workflow context."""
        return ".".join(self._workflow_stack) if self._workflow_stack else ""

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        self._workflow_stack.append(name)
        context = self._get_context()
        self._logger.info("Starting workflow: %s", context)

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        context = self._get_context()
        self._logger.info("Completed workflow: %s", context)
        if self._workflow_stack:
            self._workflow_stack.pop()

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
        context = self._get_context()
        if progress.description:
            msg = f"[{context}] {progress.description}"
        else:
            msg = f"[{context}] Progress update"

        if progress.percent is not None:
            msg += f" ({progress.percent:.1%})"
        elif progress.completed_items is not None and progress.total_items is not None:
            msg += f" ({progress.completed_items}/{progress.total_items})"

        self._logger.info(msg)
