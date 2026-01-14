# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the CosmosDB vector store implementation."""

from typing import Any

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential

from graphrag_vectors.vector_store import (
    VectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class CosmosDBVectorStore(VectorStore):
    """Azure CosmosDB vector storage implementation."""

    _cosmos_client: CosmosClient
    _database_client: DatabaseProxy
    _container_client: ContainerProxy

    def __init__(
        self,
        database_name: str,
        connection_string: str | None = None,
        url: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if self.id_field != "id":
            msg = "CosmosDB requires the id_field to be 'id'."
            raise ValueError(msg)
        if not connection_string and not url:
            msg = "Either connection_string or url must be provided for CosmosDB."
            raise ValueError(msg)

        self.database_name = database_name
        self.connection_string = connection_string
        self.url = url

    def connect(self) -> Any:
        """Connect to CosmosDB vector storage."""
        if self.connection_string:
            self._cosmos_client = CosmosClient.from_connection_string(
                self.connection_string
            )
        else:
            self._cosmos_client = CosmosClient(
                url=self.url, credential=DefaultAzureCredential()
            )

        self._create_database()
        self._create_container()

    def _create_database(self) -> None:
        """Create the database if it doesn't exist."""
        self._cosmos_client.create_database_if_not_exists(id=self.database_name)
        self._database_client = self._cosmos_client.get_database_client(
            self.database_name
        )

    def _delete_database(self) -> None:
        """Delete the database if it exists."""
        if self._database_exists():
            self._cosmos_client.delete_database(self.database_name)

    def _database_exists(self) -> bool:
        """Check if the database exists."""
        existing_database_names = [
            database["id"] for database in self._cosmos_client.list_databases()
        ]
        return self.database_name in existing_database_names

    def _create_container(self) -> None:
        """Create the container if it doesn't exist."""
        partition_key = PartitionKey(path=f"/{self.id_field}", kind="Hash")

        # Define the container vector policy
        vector_embedding_policy = {
            "vectorEmbeddings": [
                {
                    "path": f"/{self.vector_field}",
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
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [
                {"path": "/_etag/?"},
                {"path": f"/{self.vector_field}/*"},
            ],
        }

        # Currently, the CosmosDB emulator does not support the diskANN policy.
        try:
            # First try with the standard diskANN policy
            indexing_policy["vectorIndexes"] = [
                {"path": f"/{self.vector_field}", "type": "diskANN"}
            ]

            # Create the container and container client
            self._database_client.create_container_if_not_exists(
                id=self.index_name,
                partition_key=partition_key,
                indexing_policy=indexing_policy,
                vector_embedding_policy=vector_embedding_policy,
            )
        except CosmosHttpResponseError:
            # If diskANN fails (likely in emulator), retry without vector indexes
            indexing_policy.pop("vectorIndexes", None)

            # Create the container with compatible indexing policy
            self._database_client.create_container_if_not_exists(
                id=self.index_name,
                partition_key=partition_key,
                indexing_policy=indexing_policy,
                vector_embedding_policy=vector_embedding_policy,
            )

        self._container_client = self._database_client.get_container_client(
            self.index_name
        )

    def _delete_container(self) -> None:
        """Delete the vector store container in the database if it exists."""
        if self._container_exists():
            self._database_client.delete_container(self.index_name)

    def _container_exists(self) -> bool:
        """Check if the container name exists in the database."""
        existing_container_names = [
            container["id"] for container in self._database_client.list_containers()
        ]
        return self.index_name in existing_container_names

    def create_index(self) -> None:
        """Load documents into CosmosDB."""
        # Create a CosmosDB container on overwrite
        self._delete_container()
        self._create_container()

        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

    def load_documents(self, documents: list[VectorStoreDocument]) -> None:
        """Load documents into CosmosDB."""
        # Upload documents to CosmosDB
        for doc in documents:
            if doc.vector is not None:
                doc_json = {
                    self.id_field: doc.id,
                    self.vector_field: doc.vector,
                }
                self._container_client.upsert_item(doc_json)

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        try:
            query = f"SELECT TOP {k} c.{self.id_field}, c.{self.vector_field}, VectorDistance(c.{self.vector_field}, @embedding) AS SimilarityScore FROM c ORDER BY VectorDistance(c.{self.vector_field}, @embedding)"  # noqa: S608
            query_params = [{"name": "@embedding", "value": query_embedding}]
            items = list(
                self._container_client.query_items(
                    query=query,
                    parameters=query_params,
                    enable_cross_partition_query=True,
                )
            )
        except (CosmosHttpResponseError, ValueError):
            # Currently, the CosmosDB emulator does not support the VectorDistance function.
            # For emulator or test environments - fetch all items and calculate distance locally
            query = f"SELECT c.{self.id_field}, c.{self.vector_field} FROM c"  # noqa: S608
            items = list(
                self._container_client.query_items(
                    query=query,
                    enable_cross_partition_query=True,
                )
            )

            # Calculate cosine similarity locally (1 - cosine distance)
            from numpy import dot
            from numpy.linalg import norm

            def cosine_similarity(a, b):
                if norm(a) * norm(b) == 0:
                    return 0.0
                return dot(a, b) / (norm(a) * norm(b))

            # Calculate scores for all items
            for item in items:
                item_vector = item.get(self.vector_field, [])
                similarity = cosine_similarity(query_embedding, item_vector)
                item["SimilarityScore"] = similarity

            # Sort by similarity score (higher is better) and take top k
            items = sorted(
                items, key=lambda x: x.get("SimilarityScore", 0.0), reverse=True
            )[:k]

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=item.get(self.id_field, ""),
                    vector=item.get(self.vector_field, []),
                ),
                score=item.get("SimilarityScore", 0.0),
            )
            for item in items
        ]

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        item = self._container_client.read_item(item=id, partition_key=id)
        return VectorStoreDocument(
            id=item.get(self.id_field, ""),
            vector=item.get(self.vector_field, []),
        )

    def clear(self) -> None:
        """Clear the vector store."""
        self._delete_container()
        self._delete_database()
