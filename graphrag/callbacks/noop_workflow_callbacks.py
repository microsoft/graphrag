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
        self.logger.info("Pipeline started: %s", names)

    def pipeline_end(self, results: list[PipelineRunResult]) -> None:
        """Execute this callback to signal when the entire pipeline ends."""
        self.logger.info("Pipeline completed with %d workflows", len(results))

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        self.logger.info("Workflow started: %s", name)

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        self.logger.info("Workflow completed: %s", name)

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
        self.logger.debug("Progress: %s", str(progress))
