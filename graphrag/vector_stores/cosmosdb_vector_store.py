# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the CosmosDB vector store implementation."""

import json
from typing import Any

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential

from graphrag.model.types import TextEmbedder
from graphrag.vector_stores.base import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class CosmosDBVectoreStore(BaseVectorStore):
    """Azure CosmosDB vector storage implementation."""

    _cosmos_client: CosmosClient
    _database_client: DatabaseProxy
    _container_client: ContainerProxy

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def connect(self, **kwargs: Any) -> Any:
        """Connect to CosmosDB vector storage."""
        cosmosdb_account_url = kwargs.get("url")
        connection_string = kwargs.get("connection_string")
        if connection_string:
            self._cosmos_client = CosmosClient.from_connection_string(
                connection_string
            )
        else:
            if cosmosdb_account_url is None:
                msg = "Either connection_string or cosmosdb_accoun_url must be provided."
                raise ValueError(msg)
            self._cosmos_client = CosmosClient(
                url=cosmosdb_account_url,
                credential=DefaultAzureCredential()
            )

        database_name = kwargs.get("database_name")
        if database_name is None:
            msg = "Database name must be provided."
            raise ValueError(msg)
        self._database_name = database_name
        container_name = kwargs.get("container_name")
        if container_name is None:
            msg = "Container name must be provided."
            raise ValueError(msg)
        self._container_name = container_name

        self.vector_size = kwargs.get("vector_size", DEFAULT_VECTOR_SIZE)
        self.create_database()
        self.create_container()
    
    def create_database(self) -> None:
        """Create the database if it doesn't exist."""
        database_name = self._database_name
        self._cosmos_client.create_database_if_not_exists(
            id=database_name
        )
        self._database_client = self._cosmos_client.get_database_client(
            database_name
        )

    def delete_database(self) -> None:
        """Delete the database if it exists."""
        if self.database_exists():
            self._cosmos_client.delete_database(self._database_name)

    def database_exists(self) -> bool:
        """Check if the database exists."""
        database_name = self._database_name
        database_names = [
            database["id"] for database in self._cosmos_client.list_databases()
        ]
        return database_name in database_names

    def create_container(self) -> None:
        """Create the container if it doesn't exist."""
        database_client = self._database_client
        container_name = self._container_name
        partition_key = PartitionKey(path="/id", kind="Hash")

        # Define the container vector policy
        vector_embedding_policy = {
            "vectorEmbeddings": [
                {
                    "path": "/vector",
                    "dataType": "float32",
                    "distanceFunction": "cosine",
                    "dimensions": self.vector_size,
                }
            ]
        }

        # Define the vector indexing policy
        indexing_policy = {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {
                    "path": "/*"
                }
            ],
            "excludedPaths": [
                {
                    "path": "/_etag/?"
                },
                {
                    "path": "/vector/*"
                }
            ],
            "vectorIndexes": [
                {
                    "path": "/vector",
                    "type": "diskANN"
                }
            ]
        }

        # Create the container and container client
        database_client.create_container_if_not_exists(
            id=container_name,
            partition_key=partition_key,
            indexing_policy=indexing_policy,
            vector_embedding_policy=vector_embedding_policy,
        )
        self._container_client = database_client.get_container_client(
            container_name
        )

    def delete_container(self) -> None:
        """Delete the vector store container in the database if it exists."""
        database_client = self._database_client
        if self.container_exists():
            database_client.delete_container(self._container_name)

    def container_exists(self) -> bool:
        """Check if the container name exists in the database."""
        database_client = self._database_client
        container_names = [
            container["id"]
            for container in database_client.list_containers()
        ]
        return self._container_name in container_names
    
    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into CosmosDB."""
        # Create the CosmosDB container, if it doesn't exist
        if overwrite:
            self.delete_container()
            self.create_container()

        container_client = self._container_client
        if container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        # Upload documents to CosmosDB
        for doc in documents:
            if doc.vector is not None:
                doc_json = {
                    "id": doc.id,
                    "vector": doc.vector,
                    "text": doc.text,
                    "attributes": json.dumps(doc.attributes),
                }
                container_client.upsert_item(doc_json)
    
    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by a list of ids."""
        if include_ids is None or len(include_ids) == 0:
            self.query_filter = None
            # Returning to keep consistency with other methods, but not needed
            return self.query_filter
        return None
    
    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        container_client = self._container_client
        if container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)
        
        query = f"SELECT TOP {k} c.id, VectorDistance(c.vector, @embedding) AS SimilarityScore FROM c ORDER BY VectorDistance(c.vector, @embedding)"  # noqa: S608
        query_params = [
            {"name": "@embedding", "value": query_embedding}
        ]
        items = container_client.query_items(
            query=query,
            parameters=query_params,
            enable_cross_partition_query=True,
        )
        
        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=item.get("id", ""),
                    text=item.get("text", ""),
                    vector=item.get("vector", []),
                    attributes=(json.loads(item.get("attributes", "{}"))),
                ),
                score=item.get("SimilarityScore", 0.0),
            )
            for item in items
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
    
    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        container_client = self._container_client
        if container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)
        
        item = container_client.read_item(item=id, partition_key=id)
        return VectorStoreDocument(
            id=item.get("id", ""),
            vector=item.get("vector", []),
            text=item.get("text", ""),
            attributes=(json.loads(item.get("attributes", "{}"))),
        )