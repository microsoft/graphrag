# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for vector stores."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from graphrag_vectors.types import TextEmbedder


@dataclass
class VectorStoreDocument:
    """A document that is stored in vector storage."""

    id: str | int
    """unique id for the document"""

    vector: list[float] | None


@dataclass
class VectorStoreSearchResult:
    """A vector storage search result."""

    document: VectorStoreDocument
    """Document that was found."""

    score: float
    """Similarity score between -1 and 1. Higher is more similar."""


class VectorStore(ABC):
    """The base class for vector storage data-access classes."""

    def __init__(
        self,
        index_prefix: str | None = None,
        index_name: str = "vector_index",
        id_field: str = "id",
        vector_field: str = "vector",
        vector_size: int = 3072,
        **kwargs: Any,
    ):
        self.index_name = f"{index_prefix}{index_name}" if index_prefix else index_name
        self.id_field = id_field
        self.vector_field = vector_field
        self.vector_size = vector_size

    @abstractmethod
    def connect(self) -> None:
        """Connect to vector storage."""

    @abstractmethod
    def create_index(self) -> None:
        """Create index."""

    @abstractmethod
    def load_documents(self, documents: list[VectorStoreDocument]) -> None:
        """Load documents into the vector-store."""

    @abstractmethod
    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10
    ) -> list[VectorStoreSearchResult]:
        """Perform ANN search by vector."""

    @abstractmethod
    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10
    ) -> list[VectorStoreSearchResult]:
        """Perform ANN search by text."""

    @abstractmethod
    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
