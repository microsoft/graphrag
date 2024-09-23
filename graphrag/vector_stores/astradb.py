# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Astra DB vector store implementation package."""

import json
from typing import Any

from astrapy import DataAPIClient
from typing_extensions import override

from graphrag.model.types import TextEmbedder

from .base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class AstraDBVectorStore(BaseVectorStore):
    """The Astra DB vector storage implementation."""

    @override
    def connect(
        self,
        *,
        token: str | None = None,
        database_id: str | None = None,
        namespace: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Connect to the Astra DB database.

        Parameters
        ----------
        token :
            The Astra DB application token (AstraCS:xyz...).
        database_id :
            The database ID or the corresponding API Endpoint.
        namespace :
            The database namespace. If not provided, an environment-specific default
            namespace is used.
        **kwargs :
            Additional arguments passed to the ``DataAPIClient.get_database`` method.
        """
        self.db_connection = DataAPIClient(token).get_database(
            database_id, namespace=namespace, **kwargs
        )

    @override
    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        if overwrite:
            self.db_connection.drop_collection(self.collection_name)

        if not documents:
            return

        if not self.document_collection or overwrite:
            dimension = DEFAULT_VECTOR_SIZE
            for doc in documents:
                if doc.vector:
                    dimension = len(doc.vector)
                    break
            self.document_collection = self.db_connection.create_collection(
                self.collection_name,
                dimension=dimension,
                check_exists=False,
            )

        batch = [
            {
                "content": doc.text,
                "_id": doc.id,
                "$vector": doc.vector,
                "metadata": json.dumps(doc.attributes),
            }
            for doc in documents
            if doc.vector is not None
        ]

        if batch and len(batch) > 0:
            self.document_collection.insert_many(batch)

    @override
    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        if include_ids is None or len(include_ids) == 0:
            self.query_filter = {}
        else:
            self.query_filter = {"_id": {"$in": include_ids}}
        return self.query_filter

    @override
    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        response = self.document_collection.find(
            filter=self.query_filter or {},
            projection={
                "_id": True,
                "content": True,
                "metadata": True,
                "$vector": True,
            },
            limit=k,
            include_similarity=True,
            sort={"$vector": query_embedding},
        )
        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc["_id"],
                    text=doc["content"],
                    vector=doc["$vector"],
                    attributes=doc["metadata"],
                ),
                score=doc["$similarity"],
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
