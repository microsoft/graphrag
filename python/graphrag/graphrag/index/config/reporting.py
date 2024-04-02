# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing 'PipelineReportingConfig', 'PipelineFileReportingConfig' and 'PipelineConsoleReportingConfig' models."""

from __future__ import annotations

from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field


class PipelineReportingType(str, Enum):
    """Represent the reporting configuration type for the pipeline."""

    file = "file"
    """The file reporting configuration type."""
    console = "console"
    """The console reporting configuration type."""
    blob = "blob"
    """The blob reporting configuration type."""


T = TypeVar("T")


class PipelineReportingConfig(BaseModel, Generic[T]):
    """Represent the reporting configuration for the pipeline."""

    type: T


class PipelineFileReportingConfig(
    PipelineReportingConfig[Literal[PipelineReportingType.file]]
):
    """Represent the file reporting configuration for the pipeline."""

    type: Literal[PipelineReportingType.file] = PipelineReportingType.file
    """The type of reporting."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the reporting.", default=None
    )
    """The base directory for the reporting."""


class PipelineConsoleReportingConfig(
    PipelineReportingConfig[Literal[PipelineReportingType.console]]
):
    """Represent the console reporting configuration for the pipeline."""

    type: Literal[PipelineReportingType.console] = PipelineReportingType.console
    """The type of reporting."""


class PipelineBlobReportingConfig(
    PipelineReportingConfig[Literal[PipelineReportingType.blob]]
):
    """Represents the blob reporting configuration for the pipeline."""

    type: Literal[PipelineReportingType.blob] = PipelineReportingType.blob
    """The type of reporting."""

    connection_string: str = pydantic_Field(
        description="The blob reporting connection string for the reporting.",
        default=None,
    )
    """The blob reporting connection string for the reporting."""

    container_name: str = pydantic_Field(
        description="The container name for reporting", default=None
    )
    """The container name for reporting"""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the reporting.", default=None
    )
    """The base directory for the reporting."""


PipelineReportingConfigTypes = (
    PipelineFileReportingConfig
    | PipelineConsoleReportingConfig
    | PipelineBlobReportingConfig
)
