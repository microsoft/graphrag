# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine graph embed package root."""

from graphrag.index.operations.embed_graph.embed_graph import (
    EmbedGraphStrategyType,
    embed_graph,
)
from graphrag.index.operations.embed_graph.typing import NodeEmbeddings

__all__ = ["EmbedGraphStrategyType", "NodeEmbeddings", "embed_graph"]
