# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A simple WorkflowCallbacks implementation that uses standard logging."""

import logging

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.logger.progress import Progress


class LoggingWorkflowCallbacks(WorkflowCallbacks):
    """A WorkflowCallbacks implementation that forwards all events to standard logging."""

    def __init__(self, logger_name: str = "graphrag"):
        """Initialize the logging workflow callbacks."""
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

    def error(
        self,
        message: str,
        cause: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Handle when an error occurs."""
        # Create error message with details
        full_message = message
        if details:
            full_message = f"{message} details={details}"

        extra = {}
        if stack:
            extra["stack"] = stack
        if details:
            extra["details"] = details

        self.logger.error(full_message, exc_info=cause if cause else None, extra=extra)

    def warning(self, message: str, details: dict | None = None) -> None:
        """Handle when a warning occurs."""
        full_message = message
        if details:
            full_message = f"{message} details={details}"

        extra = {}
        if details:
            extra["details"] = details

        self.logger.warning(full_message, extra=extra)

    def log(self, message: str, details: dict | None = None) -> None:
        """Handle when a log message occurs."""
        full_message = message
        if details:
            full_message = f"{message} details={details}"

        extra = {}
        if details:
            extra["details"] = details

        self.logger.info(full_message, extra=extra)
