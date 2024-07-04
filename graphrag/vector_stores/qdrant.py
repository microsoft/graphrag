# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Qdrant vector storage implementation package."""

from typing import Any

from qdrant_client import QdrantClient, models

from graphrag.model.types import TextEmbedder

from .base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

TEXT_PAYLOAD_KEY = "_text"
METDATA_PAYLOAD_KEY = "_metadata"


class QdrantError(Exception):
    """An exception class for Qdrant errors."""

class QdrantVectorStore(BaseVectorStore):
    """The Qdrant vector storage implementation."""

    def connect(self, **kwargs: Any) -> Any:
        """Connect to the vector storage."""
        if self.collection_name is None:
            msg = "collection_name not set"
            raise ValueError(msg)

        self._default_vector_size = kwargs.pop(
            "default_vector_size", DEFAULT_VECTOR_SIZE
        )
        self._vector_params = kwargs.pop("vector_params", {})
        self._collection_config = kwargs.pop("collection_config", {})
        self._text_payload_key = kwargs.pop("text_payload_key", TEXT_PAYLOAD_KEY)
        self._metadata_payload_key = kwargs.pop(
            "metadata_payload_key", METDATA_PAYLOAD_KEY
        )

        self.db_connection = QdrantClient(**kwargs)

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        if self.db_connection is None:
            msg = "db_connection not set. Call connect() first."
            raise QdrantError(msg)

        collection_exists = self.db_connection.collection_exists(self.collection_name)

        if collection_exists and overwrite:
            self.db_connection.delete_collection(self.collection_name)
            collection_exists = False

        if not collection_exists:
            first_doc_embedding = documents[0].vector
            dimension = (
                len(first_doc_embedding)
                if first_doc_embedding
                else self._default_vector_size
            )

            self.db_connection.create_collection(
                self.collection_name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE,
                    **self._vector_params,
                ),
                **self._collection_config,
            )

        points = [
            models.PointStruct(
                id=document.id,
                vector=document.vector,
                payload={
                    self._text_payload_key: document.text,
                    self._metadata_payload_key: document.attributes,
                },
            )
            for document in documents
            if document.vector is not None
        ]

        self.db_connection.upsert(self.collection_name, points)  # type: ignore

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        if len(include_ids) == 0:
            self.query_filter = None
        else:
            self.query_filter = models.Filter(
                must=[
                    models.HasIdCondition(has_id=include_ids),  # type: ignore
                ]
            )
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self.db_connection is None:
            msg = "db_connection not set. Call connect() first."
            raise QdrantError(msg)

        results = self.db_connection.search(
            self.collection_name,
            query_vector=query_embedding,
            limit=k,
            query_filter=self.query_filter,
            with_payload=True,
            with_vectors=False,
            **kwargs,
        )
        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=result.id,
                    text=result.payload.get(self._text_payload_key, "") if result.payload else "",
                    vector=result.vector, # type: ignore
                    attributes=result.payload.get(self._metadata_payload_key, {}) if result.payload else {},
                ),
                score=result.score,
            )
            for result in results
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []
