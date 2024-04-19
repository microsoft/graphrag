# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import (
    DEFAULT_NODE2VEC_ENABLED,
    DEFAULT_NODE2VEC_ITERATIONS,
    DEFAULT_NODE2VEC_NUM_WALKS,
    DEFAULT_NODE2VEC_RANDOM_SEED,
    DEFAULT_NODE2VEC_WALK_LENGTH,
    DEFAULT_NODE2VEC_WINDOW_SIZE,
)


class EmbedGraphConfigModel(BaseModel):
    """The default configuration section for Node2Vec."""

    enabled: bool = Field(
        description="A flag indicating whether to enable node2vec.",
        default=DEFAULT_NODE2VEC_ENABLED,
    )
    num_walks: int = Field(
        description="The node2vec number of walks.", default=DEFAULT_NODE2VEC_NUM_WALKS
    )
    walk_length: int = Field(
        description="The node2vec walk length.", default=DEFAULT_NODE2VEC_WALK_LENGTH
    )
    window_size: int = Field(
        description="The node2vec window size.", default=DEFAULT_NODE2VEC_WINDOW_SIZE
    )
    iterations: int = Field(
        description="The node2vec iterations.", default=DEFAULT_NODE2VEC_ITERATIONS
    )
    random_seed: int = Field(
        description="The node2vec random seed.", default=DEFAULT_NODE2VEC_RANDOM_SEED
    )
    strategy: dict | None = Field(
        description="The graph embedding strategy override.", default=None
    )

    def resolved_strategy(self) -> dict:
        """Get the resolved node2vec strategy."""
        from graphrag.index.verbs.graph.embed import EmbedGraphStrategyType

        return self.strategy or {
            "type": EmbedGraphStrategyType.node2vec,
            "num_walks": self.num_walks,
            "walk_length": self.walk_length,
            "window_size": self.window_size,
            "iterations": self.iterations,
            "random_seed": self.iterations,
        }
