# Copyright (c) 2024 Microsoft Corporation.

"""A package containing vector-storage implementations."""

from .base import BaseVectorStore, VectorStoreDocument, VectorStoreSearchResult

__all__ = ["BaseVectorStore", "VectorStoreDocument", "VectorStoreSearchResult"]
