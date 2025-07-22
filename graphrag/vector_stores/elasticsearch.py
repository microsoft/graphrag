# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The ElasticSearch vector storage implementation package."""

import json
from typing import Any

import numpy as np
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk

from graphrag.data_model.types import TextEmbedder
from graphrag.vector_stores.base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


def _create_index_settings(vector_dim: int) -> dict:
    """Create ElasticSearch index settings with dynamic vector dimensions."""
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "text": {"type": "text"},
                "vector": {
                    "type": "dense_vector",
                    "dims": vector_dim,
                    "index": True,
                    "similarity": "cosine",
                },
                "attributes": {"type": "text"},
            }
        },
    }


class ElasticSearchVectorStore(BaseVectorStore):
    """ElasticSearch vector storage implementation."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def connect(self, **kwargs: Any) -> None:
        """Connect to the vector storage."""
        self.db_connection = Elasticsearch(
            hosts=[kwargs.get("url", "http://localhost:9200")]
        )
        if self.collection_name and self.db_connection.indices.exists(
            index=self.collection_name
        ):
            pass

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into vector storage."""
        if self.db_connection is None:
            msg = "Must connect to ElasticSearch before loading documents"
            raise RuntimeError(msg)

        data = [
            {
                "id": document.id,
                "text": document.text,
                "vector": document.vector,
                "attributes": json.dumps(document.attributes),
            }
            for document in documents
            if document.vector is not None
        ]

        if len(data) == 0:
            data = None

        if overwrite:
            if self.db_connection.indices.exists(index=self.collection_name):
                self.db_connection.indices.delete(index=self.collection_name)

            if data:
                vector_dim = len(data[0]["vector"])
                index_settings = _create_index_settings(vector_dim)

                self.db_connection.indices.create(
                    index=self.collection_name,
                    body=index_settings,
                )
                actions = [
                    {
                        "_index": self.collection_name,
                        "_id": str(doc["id"]),
                        "_source": doc,
                    }
                    for doc in data
                ]
                bulk(self.db_connection, actions)
                self.db_connection.indices.refresh(index=self.collection_name)
            else:
                default_settings = _create_index_settings(1536)
                self.db_connection.indices.create(
                    index=self.collection_name,
                    body=default_settings,
                )
        else:
            if not self.db_connection.indices.exists(index=self.collection_name):
                if data:
                    vector_dim = len(data[0]["vector"])
                    index_settings = _create_index_settings(vector_dim)
                else:
                    index_settings = _create_index_settings(1536)

                self.db_connection.indices.create(
                    index=self.collection_name,
                    body=index_settings,
                )
            if data:
                actions = [
                    {
                        "_index": self.collection_name,
                        "_id": str(doc["id"]),
                        "_source": doc,
                    }
                    for doc in data
                ]
                bulk(self.db_connection, actions)
                self.db_connection.indices.refresh(index=self.collection_name)

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        if len(include_ids) == 0:
            self.query_filter = None
        else:
            self.query_filter = {
                "terms": {"id": [str(doc_id) for doc_id in include_ids]}
            }
        return self.query_filter

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self.db_connection is None:
            msg = "Must connect to ElasticSearch before searching"
            raise RuntimeError(msg)

        query = {
            "knn": {
                "field": "vector",
                "query_vector": query_embedding,
                "k": k,
                "num_candidates": min(k * 10, 10000),
            },
            "_source": ["id", "text", "vector", "attributes"],
        }

        if self.query_filter:
            query["query"] = self.query_filter

        response = self.db_connection.search(
            index=self.collection_name,
            body=query,
        )

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=hit["_source"]["id"],
                    text=hit["_source"]["text"],
                    vector=hit["_source"]["vector"],
                    attributes=json.loads(hit["_source"]["attributes"]),
                ),
                score=hit["_score"],
            )
            for hit in response["hits"]["hits"]
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        query_embedding = text_embedder(text)
        if query_embedding is not None:
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()
            return self.similarity_search_by_vector(query_embedding, k)
        return []

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        if self.db_connection is None:
            msg = "Must connect to ElasticSearch before searching"
            raise RuntimeError(msg)

        try:
            response = self.db_connection.get(
                index=self.collection_name,
                id=str(id),
            )
            source = response["_source"]
            return VectorStoreDocument(
                id=source["id"],
                text=source["text"],
                vector=source["vector"],
                attributes=json.loads(source["attributes"]),
            )
        except NotFoundError:
            return VectorStoreDocument(id=id, text=None, vector=None)
