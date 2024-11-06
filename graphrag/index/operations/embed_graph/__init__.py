# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine graph embed package root."""

from .embed_graph import EmbedGraphStrategyType, embed_graph
from .typing import NodeEmbeddings

__all__ = ["EmbedGraphStrategyType", "NodeEmbeddings", "embed_graph"]
