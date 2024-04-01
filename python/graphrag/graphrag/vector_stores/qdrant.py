#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A package containing the Qdrant vector store implementation."""

from typing import Any

from qdrant_client import QdrantClient  # type: ignore
from qdrant_client.http import models  # type: ignore
from qdrant_client.models import Distance, VectorParams  # type: ignore

from graphrag.model.types import TextEmbedder

from .base import BaseVectorStore, VectorStoreDocument, VectorStoreSearchResult


class Qdrant(BaseVectorStore):
    """The Qdrant vector storage implementation."""

    def connect(self, **kwargs: Any) -> Any:
        """Connect to the Qdrant vector store."""
        url = kwargs.get("url", None)
        port = kwargs.get("port", 6333)

        api_key = kwargs.get("api_key", None)
        timeout = kwargs.get("timeout", 1000)
        self.vector_size = kwargs.get("vector_size", 1536)

        if url:
            https = kwargs.get("https", "https://" in url)
            self.db_connection = QdrantClient(
                url=url, port=port, api_key=api_key, https=https, timeout=timeout
            )
        else:
            # create in-memory db
            self.db_connection = QdrantClient(":memory:")

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into the vector store."""
        if overwrite:
            self.db_connection.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=(
                        len(documents[0].vector)
                        if len(documents) > 0 and documents[0].vector
                        else self.vector_size
                    ),
                    distance=Distance.COSINE,
                ),
            )

        self.db_connection.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                ids=[doc.id for doc in documents],
                vectors=[doc.vector if doc.vector else [] for doc in documents],
                payloads=[{"text": doc.text, **doc.attributes} for doc in documents],
            ),
        )

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        self.query_filter = models.Filter(
            must=[
                models.HasIdCondition(has_id=include_ids),  # type: ignore
            ],
        )
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        docs = self.db_connection.search(
            collection_name=self.collection_name,
            query_filter=self.query_filter,
            query_vector=query_embedding,
            limit=k,
            with_vectors=True,
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc.id,
                    text=doc.payload["text"] if doc.payload else "",
                    vector=doc.vector if doc.vector else [],  # type: ignore
                    attributes=(
                        {k: v for k, v in doc.payload.items() if k != "text"}
                        if doc.payload
                        else {}
                    ),
                ),
                score=1 - abs(doc.score),
            )
            for doc in docs
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a text-based similarity search."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(
                query_embedding=query_embedding, k=k
            )
        return []
