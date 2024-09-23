# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class QueryContextConfig(BaseModel):
    """The default configuration section for Cache."""
    files: list[str] = Field(
        description="The list of the files on which query should be run.",
        default=[]
    )