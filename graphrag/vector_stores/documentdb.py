# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the DocumentDB vector store implementation."""

import json
from typing import Any, List, Union
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, Json

from graphrag.model.types import TextEmbedder
from graphrag.vector_stores.base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

class DocumentDBVectorStore(BaseVectorStore):
    """Microsoft DocumentDB (PostgreSQL) vector storage implementation."""

    _connection: psycopg2.extensions.connection
    _cursor: psycopg2.extensions.cursor

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.db_name = kwargs.get("database_name", "documentdb")

        kind = kwargs.get("kind", "vector-ivf")  # Possible values: vector-hnsw, vector-ivf.
        similarity = kwargs.get("similarity", "COS")  # COS for cosine similarity, L2 for Euclidean distance, or IP for inner product.
        dimensions = kwargs.get("dimensions", DEFAULT_VECTOR_SIZE)
        num_lists = kwargs.get("numLists", 100)  # Only IVF index requires this parameter.
        m = kwargs.get("m", 16)  # Only HNSW index requires this parameter.
        ef_construction = kwargs.get("efConstruction", 64)  # Only HNSW index requires this parameter.

        self.vector_options = kwargs.get("vector_options", {
            "kind": kind,
            "similarity": similarity,
            "dimensions": dimensions,
            "numLists": num_lists,
            "m": m,
            "efConstruction": ef_construction
        })

    def connect(self, **kwargs: Any) -> None:
        """Connect to DocumentDB (PostgreSQL) vector storage."""
        user = kwargs.get("user")
        password = kwargs.get("password")
        host = kwargs.get("host")
        port = kwargs.get("port", 5432)

        if not all([self.db_name, user, password, host]):
            raise ValueError("Database credentials must be provided.")

        self._connection = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port
        )
        self._cursor = self._connection.cursor(cursor_factory=RealDictCursor)

        set_first = 'SET search_path TO documentdb_api, documentdb_core;'
        self._cursor.execute(set_first)
        self._connection.commit()

        self.document_collection = self.create_collection()

    def load_documents(self, documents: List[VectorStoreDocument], overwrite: bool = True) -> None:
        """Load documents into vector storage."""
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
            drop_query = sql.SQL("SELECT * FROM documentdb_api.drop_collection(%s, %s);")
            create_query = sql.SQL("SELECT * FROM documentdb_api.create_collection(%s, %s);")

            self._cursor.execute(drop_query, [self.db_name, self.collection_name])
            self._connection.commit()
            self._cursor.execute(create_query, [self.db_name, self.collection_name])
            self._connection.commit()

            self.create_vector_index("vector_index", "vector")

        if data:
            for doc in data:
                insert_query = sql.SQL("SELECT documentdb_api.insert_one(%s, %s, %s);")
                self._cursor.execute(insert_query, [self.db_name, self.collection_name, Json(doc)])
                self._connection.commit()

    def create_collection(self) -> str:
        """Create a collection in the database."""
        create_collection_query = sql.SQL("SELECT * FROM documentdb_api.create_collection(%s, %s);")
        self._cursor.execute(create_collection_query, [self.db_name, self.collection_name])
        self._connection.commit()

        self.create_vector_index("vector_index", "vector")
        return self.collection_name

    def create_vector_index(self, index_name: str, index_field: str) -> None:
        """Create an index on the collection."""
        index_query = {
            "createIndexes": self.collection_name,
            "indexes": [
                {
                    "name": index_name,
                    "key": {
                        index_field: "cosmosSearch"
                    },
                    "cosmosSearchOptions": self.vector_options
                }
            ]
        }
        
        # see bug issue: https://github.com/microsoft/documentdb/issues/63
        create_index_query = sql.SQL("SELECT documentdb_api_internal.create_indexes_non_concurrently(%s, %s, true);")
        self._cursor.execute(create_index_query, [self.db_name, Json(index_query)])
        self._connection.commit()

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by id."""
        if len(include_ids) == 0:
            self.query_filter = None
        else:
            if isinstance(include_ids[0], str):
                self.query_filter = {
                    "id": {
                        "$in": [f"'{id}'" for id in include_ids]
                    }
                }
            else:
                self.query_filter = {
                    "id": {
                        "$in": include_ids
                    }
                }

        return self.query_filter

    def similarity_search_by_vector(self, query_embedding: List[float], k: int = 10, **kwargs: Any) -> List[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        search_filter = {
            "aggregate": self.collection_name,
            "pipeline": [
                {
                    "$search": {
                        "cosmosSearch": {
                            "vector": query_embedding,
                            "path": "vector",
                            "k": k,
                        },
                        "returnStoredSource": True
                    }
                }
            ],
            "cursor": {
                "batchSize": k
            }
        }

        if self.query_filter:
            search_filter["pipeline"].insert(0, {"filter": self.query_filter})

        self._cursor = self._connection.cursor()
        search_query = sql.SQL("SELECT cursorpage->>'cursor.firstBatch' FROM documentdb_api.aggregate_cursor_first_page(%s, %s);")
        self._cursor.execute(search_query, [self.db_name, Json(search_filter)])
        results = self._cursor.fetchall()
        docs = [json.loads(result[0]) for result in results if result[0]]

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc["id"],
                    text=doc["text"],
                    vector=doc["vector"],
                    attributes=json.loads(doc["attributes"]),
                ),
                score=abs(float(doc['__cosmos_meta__']['score'])),
            )
            for doc in docs[0]
        ]

    def similarity_search_by_text(self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any) -> List[VectorStoreSearchResult]:
        """Perform a similarity search using a given input text."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(query_embedding, k)
        return []

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        find_filter = {
            "find": self.collection_name,
            "filter": {
                "id": id
            }
        }

        self._cursor = self._connection.cursor()
        search_query = sql.SQL("SELECT cursorpage->>'cursor.firstBatch' FROM documentdb_api.find_cursor_first_page(%s, %s);")
        self._cursor.execute(search_query, [self.db_name, Json(find_filter)])
        result = self._cursor.fetchone()
        doc = json.loads(result[0]) if result and result[0] else None

        if doc:
            return VectorStoreDocument(
                id=doc[0]["id"],
                text=doc[0]["text"],
                vector=doc[0]["vector"],
                attributes=json.loads(doc[0]["attributes"]),
            )
        return VectorStoreDocument(id=id, text=None, vector=None)