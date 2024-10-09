# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class EmbedGraphConfig(BaseModel):
    """The default configuration section for Node2Vec."""

    enabled: bool = Field(
        description="A flag indicating whether to enable node2vec.",
        default=defs.NODE2VEC_ENABLED,
    )
    num_walks: int = Field(
        description="The node2vec number of walks.", default=defs.NODE2VEC_NUM_WALKS
    )
    walk_length: int = Field(
        description="The node2vec walk length.", default=defs.NODE2VEC_WALK_LENGTH
    )
    window_size: int = Field(
        description="The node2vec window size.", default=defs.NODE2VEC_WINDOW_SIZE
    )
    iterations: int = Field(
        description="The node2vec iterations.", default=defs.NODE2VEC_ITERATIONS
    )
    random_seed: int = Field(
        description="The node2vec random seed.", default=defs.NODE2VEC_RANDOM_SEED
    )
    strategy: dict | None = Field(
        description="The graph embedding strategy override.", default=None
    )

    def resolved_strategy(self) -> dict:
        """Get the resolved node2vec strategy."""
        from graphrag.index.operations.embed_graph import (
            EmbedGraphStrategyType,
        )

        return self.strategy or {
            "type": EmbedGraphStrategyType.node2vec,
            "num_walks": self.num_walks,
            "walk_length": self.walk_length,
            "window_size": self.window_size,
            "iterations": self.iterations,
            "random_seed": self.iterations,
        }
