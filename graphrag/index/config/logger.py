# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineLoggerConfig', 'PipelineFileLoggerConfig' and 'PipelineConsoleLoggerConfig' models."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from graphrag.config.enums import PipelineLoggerType

T = TypeVar("T")


class PipelineLoggerConfig(BaseModel, Generic[T]):
    """Represent the reporting configuration for the pipeline."""

    type: T


class PipelineFileLoggerConfig(PipelineLoggerConfig[Literal[PipelineLoggerType.file]]):
    """Represent the file logger configuration for the pipeline."""

    type: Literal[PipelineLoggerType.file] = PipelineLoggerType.file
    """The type of logger."""

    base_dir: str = Field(description="The base directory for the logger.", default="")
    """The base directory for the logger."""


class PipelineConsoleLoggerConfig(
    PipelineLoggerConfig[Literal[PipelineLoggerType.console]]
):
    """Represent the console logger configuration for the pipeline."""

    type: Literal[PipelineLoggerType.console] = PipelineLoggerType.console
    """The type of logger."""


class PipelineBlobLoggerConfig(PipelineLoggerConfig[Literal[PipelineLoggerType.blob]]):
    """Represents the blob logger configuration for the pipeline."""

    type: Literal[PipelineLoggerType.blob] = PipelineLoggerType.blob
    """The type of logger."""

    connection_string: str | None = Field(
        description="The blob logger connection string for the logger.",
        default=None,
    )
    """The blob logger connection string for the logger."""

    container_name: str = Field(
        description="The container name for the logger.", default=""
    )
    """The container name for the logger."""

    storage_account_blob_url: str | None = Field(
        description="The storage account blob url for the logger.", default=None
    )
    """The storage account blob url for the logger."""

    base_dir: str = Field(description="The base directory for the logger.", default="")
    """The base directory for the logger."""


PipelineReportingConfigTypes = (
    PipelineFileLoggerConfig | PipelineConsoleLoggerConfig | PipelineBlobLoggerConfig
)
