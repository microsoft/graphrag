# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.index.config import PipelineReportingType
from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_REPORTING_BASE_DIR,
    DEFAULT_REPORTING_TYPE,
)


class ReportingConfigModel(BaseModel):
    """The default configuration section for Reporting."""

    type: PipelineReportingType = Field(
        description="The reporting type to use.", default=DEFAULT_REPORTING_TYPE
    )
    base_dir: str = Field(
        description="The base directory for reporting.",
        default=DEFAULT_REPORTING_BASE_DIR,
    )
    connection_string: str | None = Field(
        description="The reporting connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The reporting container name to use.", default=None
    )
