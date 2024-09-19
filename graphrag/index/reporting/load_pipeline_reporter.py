# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load pipeline reporter method."""

from pathlib import Path
from typing import cast

from datashaper import WorkflowCallbacks

from graphrag.config import ReportingType
from graphrag.index.config import (
    PipelineBlobReportingConfig,
    PipelineFileReportingConfig,
    PipelineReportingConfig,
)

from .blob_workflow_callbacks import BlobWorkflowCallbacks
from .console_workflow_callbacks import ConsoleWorkflowCallbacks
from .file_workflow_callbacks import FileWorkflowCallbacks


def load_pipeline_reporter(
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
