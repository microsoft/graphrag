#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Load pipeline reporter method."""
from pathlib import Path
from typing import cast

from datashaper import WorkflowCallbacks

from graphrag.index.config import (
    PipelineBlobReportingConfig,
    PipelineFileReportingConfig,
    PipelineReportingConfig,
    PipelineReportingType,
)

from .blob_workflow_callbacks import BlobWorkflowCallbacks
from .console_workflow_callbacks import ConsoleWorkflowCallbacks
from .file_workflow_callbacks import FileWorkflowCallbacks


def load_pipeline_reporter(
    config: PipelineReportingConfig | None, root_dir: str | None
) -> WorkflowCallbacks:
    """Create a reporter for the given pipeline config."""
    config = config or PipelineFileReportingConfig(base_dir="reports")

    match config.type:
        case PipelineReportingType.file:
            config = cast(PipelineFileReportingConfig, config)
            return FileWorkflowCallbacks(
                str(Path(root_dir or "") / (config.base_dir or ""))
            )
        case PipelineReportingType.console:
            return ConsoleWorkflowCallbacks()
        case PipelineReportingType.blob:
            config = cast(PipelineBlobReportingConfig, config)
            return BlobWorkflowCallbacks(
                config.connection_string,
                config.container_name,
                base_dir=config.base_dir,
            )
        case _:
            msg = f"Unknown reporting type: {config.type}"
            raise ValueError(msg)
