#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration."""
from pydantic import BaseModel, Field


class EmbedGraphConfigModel(BaseModel):
    """The default configuration section for Node2Vec."""

    is_enabled: bool | None = Field(
        description="A flag indicating whether to enable node2vec.", default=None
    )
    num_walks: int | None = Field(
        description="The node2vec number of walks.", default=None
    )
    walk_length: int | None = Field(
        description="The node2vec walk length.", default=None
    )
    window_size: int | None = Field(
        description="The node2vec window size.", default=None
    )
    iterations: int | None = Field(description="The node2vec iterations.", default=None)
    random_seed: int | None = Field(
        description="The node2vec random seed.", default=None
    )
    strategy: dict | None = Field(
        description="The graph embedding strategy override.", default=None
    )
