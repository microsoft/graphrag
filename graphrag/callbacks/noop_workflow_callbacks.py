# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A no-op implementation of WorkflowCallbacks."""

import logging

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.logger.progress import Progress


class NoopWorkflowCallbacks(WorkflowCallbacks):
    """A no-op implementation of WorkflowCallbacks that logs all events to standard logging."""

    def __init__(self, logger_name: str = "graphrag"):
        """Initialize a logger."""
        self.logger = logging.getLogger(logger_name)

    def pipeline_start(self, names: list[str]) -> None:
        """Execute this callback to signal when the entire pipeline starts."""

    def pipeline_end(self, results: list[PipelineRunResult]) -> None:
        """Execute this callback to signal when the entire pipeline ends."""

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
