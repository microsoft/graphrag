# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class GraphDBConfig(BaseModel):
    account_name: str|None = Field(
        description="Graphdb account name",
        default=None
    )
    account_key: str|None = Field(
        description="Graphdb account key",
        default=None
    )
    username: str|None = Field(
        description="Graphdb username",
        default=None
    )
    enabled: bool = Field(
        description="Flag to enable querying into graphdb",
        default=False
    )

    cosmos_url: str|None = Field(
        description="Cosmos account url",
        default=None,
    )

    gremlin_url: str|None = Field(
        description="Gremlin db url",
        default=None,
    )