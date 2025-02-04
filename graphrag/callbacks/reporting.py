# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineReportingConfig', 'PipelineFileReportingConfig' and 'PipelineConsoleReportingConfig' models."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Generic, Literal, TypeVar, cast

from pydantic import BaseModel, Field

from graphrag.callbacks.blob_workflow_callbacks import BlobWorkflowCallbacks
from graphrag.callbacks.console_workflow_callbacks import ConsoleWorkflowCallbacks
from graphrag.callbacks.file_workflow_callbacks import FileWorkflowCallbacks
from graphrag.config.enums import ReportingType

if TYPE_CHECKING:
    from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks

T = TypeVar("T")


class PipelineReportingConfig(BaseModel, Generic[T]):
    """Represent the reporting configuration for the pipeline."""

    type: T


class PipelineFileReportingConfig(PipelineReportingConfig[Literal[ReportingType.file]]):
    """Represent the file reporting configuration for the pipeline."""

    type: Literal[ReportingType.file] = ReportingType.file
    """The type of reporting."""

    base_dir: str | None = Field(
        description="The base directory for the reporting.", default=None
    )
    """The base directory for the reporting."""


class PipelineConsoleReportingConfig(
    PipelineReportingConfig[Literal[ReportingType.console]]
):
    """Represent the console reporting configuration for the pipeline."""

    type: Literal[ReportingType.console] = ReportingType.console
    """The type of reporting."""


class PipelineBlobReportingConfig(PipelineReportingConfig[Literal[ReportingType.blob]]):
    """Represents the blob reporting configuration for the pipeline."""

    type: Literal[ReportingType.blob] = ReportingType.blob
    """The type of reporting."""

    connection_string: str | None = Field(
        description="The blob reporting connection string for the reporting.",
        default=None,
    )
    """The blob reporting connection string for the reporting."""

    container_name: str = Field(
        description="The container name for reporting", default=""
    )
    """The container name for reporting"""

    storage_account_blob_url: str | None = Field(
        description="The storage account blob url for reporting", default=None
    )
    """The storage account blob url for reporting"""

    base_dir: str | None = Field(
        description="The base directory for the reporting.", default=None
    )
    """The base directory for the reporting."""


PipelineReportingConfigTypes = (
    PipelineFileReportingConfig
    | PipelineConsoleReportingConfig
    | PipelineBlobReportingConfig
)


def create_pipeline_reporter(
    config: PipelineReportingConfig | None, root_dir: str | None
) -> WorkflowCallbacks:
    """Create a logger for the given pipeline config."""
    config = config or PipelineFileReportingConfig(base_dir="logs")

    match config.type:
        case ReportingType.file:
            config = cast("PipelineFileReportingConfig", config)
            return FileWorkflowCallbacks(
                str(Path(root_dir or "") / (config.base_dir or ""))
            )
        case ReportingType.console:
            return ConsoleWorkflowCallbacks()
        case ReportingType.blob:
            config = cast("PipelineBlobReportingConfig", config)
            return BlobWorkflowCallbacks(
                config.connection_string,
                config.container_name,
                base_dir=config.base_dir,
                storage_account_blob_url=config.storage_account_blob_url,
            )
        case _:
            msg = f"Unknown reporting type: {config.type}"
            raise ValueError(msg)
