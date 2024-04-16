# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_NODE2VEC_IS_ENABLED,
    DEFAULT_NODE2VEC_ITERATIONS,
    DEFAULT_NODE2VEC_NUM_WALKS,
    DEFAULT_NODE2VEC_RANDOM_SEED,
    DEFAULT_NODE2VEC_WALK_LENGTH,
    DEFAULT_NODE2VEC_WINDOW_SIZE,
)


class EmbedGraphConfigModel(BaseModel):
    """The default configuration section for Node2Vec."""

    is_enabled: bool | None = Field(
        description="A flag indicating whether to enable node2vec.",
        default=DEFAULT_NODE2VEC_IS_ENABLED,
    )
    num_walks: int | None = Field(
        description="The node2vec number of walks.", default=DEFAULT_NODE2VEC_NUM_WALKS
    )
    walk_length: int | None = Field(
        description="The node2vec walk length.", default=DEFAULT_NODE2VEC_WALK_LENGTH
    )
    window_size: int | None = Field(
        description="The node2vec window size.", default=DEFAULT_NODE2VEC_WINDOW_SIZE
    )
    iterations: int | None = Field(
        description="The node2vec iterations.", default=DEFAULT_NODE2VEC_ITERATIONS
    )
    random_seed: int | None = Field(
        description="The node2vec random seed.", default=DEFAULT_NODE2VEC_RANDOM_SEED
    )
    strategy: dict | None = Field(
        description="The graph embedding strategy override.", default=None
    )
