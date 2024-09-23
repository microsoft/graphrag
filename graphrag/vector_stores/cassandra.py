# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Apache Cassandra vector store implementation package."""

from typing import Any

import cassio
from cassandra.cluster import Session
from cassio.table import MetadataVectorCassandraTable
from typing_extensions import override

from graphrag.model.types import TextEmbedder

from .base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class CassandraVectorStore(BaseVectorStore):
    """The Apache Cassandra vector storage implementation."""

    @override
    def connect(
        self,
        *,
        session: Session | None = None,
        keyspace: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Connect to the Apache Cassandra database.

        Parameters
        ----------
        session :
            The Cassandra session. If not provided, it is resolved from cassio.
        keyspace :
            The Cassandra keyspace. If not provided, it is resolved from cassio.
        """
        self.db_connection = cassio.config.check_resolve_session(session)
        self.keyspace = cassio.config.check_resolve_keyspace(keyspace)

    @override
    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        if overwrite:
            self.db_connection.execute(
                f"DROP TABLE IF EXISTS {self.keyspace}.{self.collection_name};"
            )

        if not documents:
            return

        if not self.document_collection or overwrite:
            dimension = DEFAULT_VECTOR_SIZE
            for doc in documents:
                if doc.vector:
                    dimension = len(doc.vector)
                    break
            self.document_collection = MetadataVectorCassandraTable(
                table=self.collection_name,
                vector_dimension=dimension,
                primary_key_type="TEXT",
            )

        futures = [
            self.document_collection.put_async(
                row_id=doc.id,
                body_blob=doc.text,
                vector=doc.vector,
                metadata=doc.attributes,
            )
            for doc in documents
            if doc.vector
        ]

        for future in futures:
            future.result()

    @override
    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        msg = "Cassandra vector store doesn't support filtering by IDs."
        raise NotImplementedError(msg)

    @override
    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        response = self.document_collection.metric_ann_search(
            vector=query_embedding,
            n=k,
            metric="cos",
            **kwargs,
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc["row_id"],
                    text=doc["body_blob"],
                    vector=doc["vector"],
                    attributes=doc["metadata"],
                ),
                score=doc["distance"],
            )
            for doc in response
        ]

    @override
    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(
                query_embedding=query_embedding, k=k, **kwargs
            )
        return []
