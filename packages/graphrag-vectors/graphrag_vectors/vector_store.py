# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for vector stores."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from graphrag_vectors.filtering import FilterExpr
from graphrag_vectors.timestamp import (
    TIMESTAMP_FIELDS,
    _timestamp_fields_for,
    explode_timestamp,
)
from graphrag_vectors.types import TextEmbedder

# Signature for a function that explodes an ISO 8601 timestamp into
# a dict of filterable component fields keyed by "{prefix}_{suffix}".
TimestampExploder = Callable[[str, str], dict[str, str | int]]


@dataclass
class VectorStoreDocument:
    """A document that is stored in vector storage."""

    id: str | int
    """unique id for the document"""

    vector: list[float] | None
    """the vector embedding for the document"""

    data: dict[str, Any] = field(default_factory=dict)
    """additional data associated with the document"""

    create_date: str | None = None
    """optional ISO 8601 timestamp for when the document was created"""

    update_date: str | None = None
    """optional ISO 8601 timestamp for when the document was last updated"""


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
        index_name: str = "vector_index",
        id_field: str = "id",
        vector_field: str = "vector",
        create_date_field: str = "create_date",
        update_date_field: str = "update_date",
        vector_size: int = 3072,
        fields: dict[str, str] | None = None,
        timestamp_exploder: TimestampExploder = explode_timestamp,
        **kwargs: Any,
    ):
        self.index_name = index_name
        self.id_field = id_field
        self.vector_field = vector_field
        self.create_date_field = create_date_field
        self.update_date_field = update_date_field
        self.vector_size = vector_size
        self.fields = fields or {}
        self.timestamp_exploder = timestamp_exploder

        # Detect user-defined date fields, store raw value as str,
        # and register their exploded component fields.
        self.date_fields: list[str] = [
            name for name, ftype in self.fields.items() if ftype == "date"
        ]
        for name in self.date_fields:
            self.fields[name] = "str"
            self.fields.update(_timestamp_fields_for(name))

        # Auto-register built-in timestamp component fields
        self.fields.update(TIMESTAMP_FIELDS)

    @staticmethod
    def _now_iso() -> str:
        """Return the current UTC time as an ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def _prepare_document(self, document: VectorStoreDocument) -> None:
        """Enrich a document's data dict with exploded timestamp fields.

        Automatically sets create_date to now if not already provided.
        Explodes any user-defined date fields found in document.data.
        Call this during insert before extracting field values.
        """
        if document.data is None:
            document.data = {}
        if not document.create_date:
            document.create_date = self._now_iso()
        document.data.update(
            self.timestamp_exploder(document.create_date, "create_date")
        )
        if document.update_date:
            document.data.update(
                self.timestamp_exploder(document.update_date, "update_date")
            )

        # Explode user-defined date fields
        for name in self.date_fields:
            value = document.data.get(name)
            if value:
                document.data.update(self.timestamp_exploder(value, name))

    def _prepare_update(self, document: VectorStoreDocument) -> None:
        """Set update_date to now and explode its timestamp fields.

        Call this during update before persisting changes.
        """
        if document.data is None:
            document.data = {}
        if not document.update_date:
            document.update_date = self._now_iso()
        document.data.update(
            self.timestamp_exploder(document.update_date, "update_date")
        )

    @abstractmethod
    def connect(self) -> None:
        """Connect to vector storage."""

    @abstractmethod
    def create_index(self) -> None:
        """Create index."""

    @abstractmethod
    def load_documents(self, documents: list[VectorStoreDocument]) -> None:
        """Load documents into the vector-store."""

    def insert(self, document: VectorStoreDocument) -> None:
        """Insert a single document by delegating to load_documents."""
        self.load_documents([document])

    @abstractmethod
    def similarity_search_by_vector(
        self,
        query_embedding: list[float],
        k: int = 10,
        select: list[str] | None = None,
        filters: FilterExpr | None = None,
        include_vectors: bool = True,
    ) -> list[VectorStoreSearchResult]:
        """Perform ANN search by vector.

        Parameters
        ----------
        query_embedding : list[float]
            The query vector.
        k : int
            Number of results to return.
        select : list[str] | None
            Fields to include in results.
        filters : FilterExpr | None
            Optional filter expression to pre-filter candidates before search.
        include_vectors : bool
            Whether to include vector embeddings in results.
        """

    def similarity_search_by_text(
        self,
        text: str,
        text_embedder: TextEmbedder,
        k: int = 10,
        select: list[str] | None = None,
        filters: FilterExpr | None = None,
        include_vectors: bool = True,
    ) -> list[VectorStoreSearchResult]:
        """Perform a text-based similarity search."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(
                query_embedding=query_embedding,
                k=k,
                select=select,
                filters=filters,
                include_vectors=include_vectors,
            )
        return []

    @abstractmethod
    def search_by_id(
        self,
        id: str,
        select: list[str] | None = None,
        include_vectors: bool = True,
    ) -> VectorStoreDocument:
        """Search for a document by id."""

    @abstractmethod
    def count(self) -> int:
        """Return the total number of documents in the store."""

    @abstractmethod
    def remove(self, ids: list[str]) -> None:
        """Remove documents by id."""

    @abstractmethod
    def update(self, document: VectorStoreDocument) -> None:
        """Update a document in the store."""
