# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the pipeline reporter factory."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from graphrag.callbacks.blob_workflow_callbacks import BlobWorkflowCallbacks
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.callbacks.file_workflow_callbacks import FileWorkflowCallbacks
from graphrag.callbacks.s3_workflow_callbacks import S3WorkflowCallbacks
from graphrag.config.enums import ReportingType
from graphrag.config.models.reporting_config import ReportingConfig

if TYPE_CHECKING:
    from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks


def create_pipeline_reporter(
    config: ReportingConfig | None, root_dir: str | None
) -> WorkflowCallbacks:
    """Create a logger for the given pipeline config."""
    config = config or ReportingConfig(base_dir="logs", type=ReportingType.file)
    match config.type:
        case ReportingType.file:
            return FileWorkflowCallbacks(
                str(Path(root_dir or "") / (config.base_dir or ""))
            )
        case ReportingType.console:
            return ConsoleWorkflowCallbacks()
        case ReportingType.blob:
            return BlobWorkflowCallbacks(
                config.connection_string,
                config.container_name,
                base_dir=config.base_dir,
                storage_account_blob_url=config.storage_account_blob_url,
            )
        case ReportingType.s3:
            if not config.bucket_name:
                msg = "No bucket name provided for S3 storage."
                raise ValueError(msg)
            return S3WorkflowCallbacks(
                bucket_name=config.bucket_name,
                base_dir=config.prefix or "",
                log_file_name=config.base_dir,
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                region_name=config.region_name,
                endpoint_url=config.endpoint_url,
            )
