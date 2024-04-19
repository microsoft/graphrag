# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import (
    DEFAULT_REPORTING_BASE_DIR,
    DEFAULT_REPORTING_TYPE,
)
from graphrag.config.enums import ReportingType


class ReportingConfig(BaseModel):
    """The default configuration section for Reporting."""

    type: ReportingType = Field(
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
