# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating loggers."""

from pathlib import Path
from typing import cast

from datashaper import WorkflowCallbacks

from graphrag.callbacks.blob_workflow_callbacks import BlobWorkflowCallbacks
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.callbacks.file_workflow_callbacks import FileWorkflowCallbacks
from graphrag.config import ReportingType
from graphrag.index.config import (
    PipelineBlobReportingConfig,
    PipelineFileReportingConfig,
    PipelineReportingConfig,
)

from .null_progress import NullProgressLogger
from .print_progress import PrintProgressLogger
from .rich_progress import RichProgressLogger
from .types import (
    LoggerType,
    ProgressLogger,
)


def create_progress_logger(
    reporter_type: LoggerType = LoggerType.NONE,
) -> ProgressLogger:
    """Load a progress reporter.

    Parameters
    ----------
    reporter_type : {"rich", "print", "none"}, default=rich
        The type of progress reporter to load.

    Returns
    -------
    ProgressLogger
    """
    match reporter_type:
        case LoggerType.RICH:
            return RichProgressLogger("GraphRAG Indexer ")
        case LoggerType.PRINT:
            return PrintProgressLogger("GraphRAG Indexer ")
        case LoggerType.NONE:
            return NullProgressLogger()
        case _:
            msg = f"Invalid progress reporter type: {reporter_type}"
            raise ValueError(msg)


def create_pipeline_logger(
    config: PipelineReportingConfig | None, root_dir: str | None
) -> WorkflowCallbacks:
    """Create a reporter for the given pipeline config."""
    config = config or PipelineFileReportingConfig(base_dir="logs")

    match config.type:
        case ReportingType.file:
            config = cast(PipelineFileReportingConfig, config)
            return FileWorkflowCallbacks(
                str(Path(root_dir or "") / (config.base_dir or ""))
            )
        case ReportingType.console:
            return ConsoleWorkflowCallbacks()
        case ReportingType.blob:
            config = cast(PipelineBlobReportingConfig, config)
            return BlobWorkflowCallbacks(
                config.connection_string,
                config.container_name,
                base_dir=config.base_dir,
                storage_account_blob_url=config.storage_account_blob_url,
            )
        case _:
            msg = f"Unknown reporting type: {config.type}"
            raise ValueError(msg)
