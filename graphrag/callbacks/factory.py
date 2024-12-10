# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create a pipeline logger."""

from typing import ClassVar

from datashaper import WorkflowCallbacks

from graphrag.callbacks.blob_workflow_callbacks import BlobWorkflowCallbacks
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.callbacks.file_workflow_callbacks import FileWorkflowCallbacks
from graphrag.config.enums import PipelineLoggerType


class PipelineLoggerFactory:
    """A factory class for indexing pipeline logger implementations.

    Pipeline loggers are designed with callback functions that the indexing engine
    calls to log updates during the indexing process.

    Includes a method for users to register custom indexing pipeline logger implementations.
    """

    pipeline_logger_types: ClassVar[dict[str, type]] = {}

    @classmethod
    def register(cls, logger_type: str, logger: type):
        """Register a custom pipeline logger implementation."""
        cls.pipeline_logger_types[logger_type] = logger

    @classmethod
    def create_pipeline_logger(
        cls,
        pipeline_logger_type: PipelineLoggerType | str,
        kwargs: dict | None = None,
    ) -> WorkflowCallbacks:
        """Create a pipeline logger from the provided type."""
        if not kwargs:
            kwargs = {}

        match pipeline_logger_type:
            case PipelineLoggerType.blob:
                return BlobWorkflowCallbacks(**kwargs)
            case PipelineLoggerType.console:
                return ConsoleWorkflowCallbacks()
            case PipelineLoggerType.file:
                return FileWorkflowCallbacks(**kwargs)
            case _:
                if pipeline_logger_type in cls.pipeline_logger_types:
                    return cls.pipeline_logger_types[pipeline_logger_type](**kwargs)
                # Default to console logger if no match
                return ConsoleWorkflowCallbacks()
