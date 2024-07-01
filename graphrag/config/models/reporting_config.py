# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import ReportingType


class ReportingConfig(BaseModel):
    """The default configuration section for Reporting."""

    type: ReportingType = Field(
        description="The reporting type to use.", default=defs.REPORTING_TYPE
    )
    base_dir: str = Field(
        description="The base directory for reporting.",
        default=defs.REPORTING_BASE_DIR,
    )
    connection_string: str | None = Field(
        description="The reporting connection string to use.", default=None
    )
    container_name: str | None = Field(
        description="The reporting container name to use.", default=None
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.", default=None
    )
