# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine graph embedding package root."""

from graphrag.index.graph.embedding.embedding import NodeEmbeddings, embed_nod2vec

__all__ = ["NodeEmbeddings", "embed_nod2vec"]
