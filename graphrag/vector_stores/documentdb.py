# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the DocumentDB vector store implementation."""

import json
from typing import Any
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json

from graphrag.model.types import TextEmbedder
from graphrag.vector_stores.base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

class DocumentDBVectoreStore(BaseVectorStore):
    """Microsoft DocumentB (PostgreSQL) vector storage implementation."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.db_name = kwargs.get("database_name", "documentdb")
        self.vector_options = kwargs.get("vector_options", { "kind": "vector-ivf", "similarity": "COS", "dimensions": DEFAULT_VECTOR_SIZE, "numLists": 3 })

    def connect(self, **kwargs: Any) -> Any:
        """Connect to DocumentDB (PostgreSQL) vector storage."""
        user = kwargs.get("user")
        password = kwargs.get("password")
        host = kwargs.get("host")
        port = kwargs.get("port", 5432)

        if not all([self.db_name, user, password, host]):
            raise ValueError("Database credentials must be provided.")
        
        self.db_connection = psycopg2.connect(
            dbname="postgres", user=user, password=password, host=host, port=port
        )
        cursor = self.db_connection.cursor()

        # replace this with a more general solution
        x = sql.SQL("SET search_path TO documentdb_api, documentdb_core; SET documentdb_core.bsonUseEJson TO true;")
        cursor.execute(x)
        self.db_connection.commit()

        coll_query = {
            "listCollections": 1,
            "filter" : {
                "collection_name":  self.collection_name
            }
        }
        try:
            query = sql.SQL("SELECT cursorpage->>'cursor.firstBatch' FROM documentdb_api.list_collections_cursor_first_page(%s, %s);")
            cursor.execute(query, [self.db_name, Json(coll_query)])
            result = cursor.fetchone()
            if result and result[0]:
                first_batch = json.loads(result[0]) 
                if self.collection_name in first_batch:
                    self.document_collection = self.collection_name
                else:
                    self.document_collection = self.create_collection()
        except Exception as e:
            self.document_collection = self.collection_name

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
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

        # NOTE: If modifying the next section of code, ensure that the schema remains the same.
        #       The pyarrow format of the 'vector' field may change if the order of operations is changed
        #       and will break vector search.
        cursor = self.db_connection.cursor()

        if overwrite:
            drop_query = sql.SQL("SELECT * FROM documentdb_api.drop_collection(%s, %s);")
            create_query = sql.SQL("SELECT * FROM documentdb_api.create_collection(%s, %s);")

            cursor.execute(drop_query, [self.db_name, self.collection_name])
            self.db_connection.commit()
            cursor.execute(create_query, [self.db_name, self.collection_name])
            self.db_connection.commit()

            self.create_vector_index("vector_index", "vector")
            
        if data:
            for doc in data:
                insert_query = sql.SQL("SELECT * FROM documentdb_api.insert_document(%s, %s, %s, %s, %s);")
                cursor.execute(insert_query, [self.db_name, self.collection_name, Json(doc)])
                self.db_connection.commit()

    def create_collection(self) -> str:
        """Create a collection in the database."""
        cursor = self.db_connection.cursor()
        create_collection_query = sql.SQL("SELECT * FROM documentdb_api.create_collection(%s, %s);")
        cursor.execute(create_collection_query, [self.db_name, self.collection_name])
        self.db_connection.commit()

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
        cursor = self.db_connection.cursor()
        # create_index_query = sql.SQL("SELECT documentdb_api.create_indexes_background(%s, %s);")
        create_index_query = sql.SQL("SELECT documentdb_api_internal.create_indexes_non_concurrently(%s, %s, true);")
        cursor.execute(create_index_query, [self.db_name, Json(index_query)])
        self.db_connection.commit()

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

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
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

        cursor = self.db_connection.cursor()
        search_query = sql.SQL("SELECT cursorpage->>'cursor.firstBatch' FROM documentdb_api.aggregate_cursor_first_page(%s, %s);")
        cursor.execute(search_query, [self.db_name, Json(search_filter)])
        results = cursor.fetchall()
        docs = [json.loads(result[0]) for result in results if result[0]]

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=doc["id"],
                    text=doc["text"],
                    vector=doc["vector"],
                    attributes=json.loads(doc["attributes"]),
                ),
                score=1 - abs(float(doc["_distance"])),
            )
            for doc in docs
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
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

        cursor = self.db_connection.cursor()
        search_query = sql.SQL("SELECT cursorpage->>'cursor.firstBatch' FROM documentdb_api.find_cursor_first_page(%s, %s);")
        cursor.execute(search_query, [self.db_name, Json(find_filter)])
        result = cursor.fetchone()
        doc = json.loads(result[0]) if result and result[0] else None
        
        if doc:
            return VectorStoreDocument(
                id=doc[0]["id"],
                text=doc[0]["text"],
                vector=doc[0]["vector"],
                attributes=json.loads(doc[0]["attributes"]),
            )
        return VectorStoreDocument(id=id, text=None, vector=None)


if __name__ == "__main__":
    from graphrag.model.entity import Entity
    entities = [
        Entity(
            id="2da37c7a-50a8-44d4-aa2c-fd401e19976c",
            short_id="sid1",
            title="t1",
            rank=2,
        ),
        Entity(
            id="c4f93564-4507-4ee4-b102-98add401a965",
            short_id="sid2",
            title="t22",
            rank=4,
        ),
        Entity(
            id="7c6f2bc9-47c9-4453-93a3-d2e174a02cd9",
            short_id="sid3",
            title="t333",
            rank=1,
        ),
        Entity(
            id="8fd6d72a-8e9d-4183-8a97-c38bcc971c83",
            short_id="sid4",
            title="t4444",
            rank=3,
        ),
    ]
    documents = [VectorStoreDocument(id=entity.id, text=entity.title, vector=[0]) for entity in entities]


    kwargs = {
        "collection_name": "default",
        "database_name": "documentdb",
        "vector_options": { "kind": "vector-ivf", "similarity": "COS", "dimensions": DEFAULT_VECTOR_SIZE, "numLists": 3 }
    }

    store = DocumentDBVectoreStore(**kwargs)
    store.connect(**{
        "user": "admin",
        "password": "admin",
        "host": "host.docker.internal",
        "port": 9712
    })
    store.load_documents(documents, overwrite=False)
    store.search_by_id("1")