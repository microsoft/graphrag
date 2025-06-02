# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base class for workflow callbacks that inherit from logging.Handler."""

import logging
from typing import Any

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.logger.progress import Progress


class WorkflowHandlerBase(logging.Handler, WorkflowCallbacks):
    """Base class for workflow callbacks that inherit from logging.Handler."""

    def __init__(self, level: int = logging.NOTSET):
        """Initialize the handler."""
        super().__init__(level)
        
    def pipeline_start(self, names: list[str]) -> None:
        """Execute this callback to signal when the entire pipeline starts."""
        record = logging.LogRecord(
            name="graphrag.pipeline",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Pipeline started: %s",
            args=(names,),
            exc_info=None,
        )
        self.emit(record)

    def pipeline_end(self, results: list[PipelineRunResult]) -> None:
        """Execute this callback to signal when the entire pipeline ends."""
        record = logging.LogRecord(
            name="graphrag.pipeline",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Pipeline completed with %d workflows",
            args=(len(results),),
            exc_info=None,
        )
        self.emit(record)

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        record = logging.LogRecord(
            name="graphrag.workflow",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Workflow started: %s",
            args=(name,),
            exc_info=None,
        )
        self.emit(record)

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        record = logging.LogRecord(
            name="graphrag.workflow",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Workflow completed: %s",
            args=(name,),
            exc_info=None,
        )
        self.emit(record)

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
        record = logging.LogRecord(
            name="graphrag.progress",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="Progress: %s",
            args=(str(progress),),
            exc_info=None,
        )
        self.emit(record)

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
        
        record = logging.LogRecord(
            name="graphrag.error",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=full_message,
            args=(),
            exc_info=(type(cause), cause, None) if cause else None,
        )
        
        # Add custom attributes for stack and details
        if stack:
            record.stack = stack  # type: ignore
        if details:
            record.details = details  # type: ignore
            
        self.emit(record)

    def warning(self, message: str, details: dict | None = None) -> None:
        """Handle when a warning occurs."""
        full_message = message
        if details:
            full_message = f"{message} details={details}"
            
        record = logging.LogRecord(
            name="graphrag.warning",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg=full_message,
            args=(),
            exc_info=None,
        )
        
        if details:
            record.details = details  # type: ignore
            
        self.emit(record)

    def log(self, message: str, details: dict | None = None) -> None:
        """Handle when a log message occurs."""
        full_message = message
        if details:
            full_message = f"{message} details={details}"
            
        record = logging.LogRecord(
            name="graphrag.log",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=full_message,
            args=(),
            exc_info=None,
        )
        
        if details:
            record.details = details  # type: ignore
            
        self.emit(record)