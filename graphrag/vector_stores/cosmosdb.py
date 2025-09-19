# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the CosmosDB vector store implementation."""

import json
from typing import Any

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential

from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from graphrag.data_model.types import TextEmbedder
from graphrag.vector_stores.base import (
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)


class CosmosDBVectorStore(BaseVectorStore):
    """Azure CosmosDB vector storage implementation."""

    _cosmos_client: CosmosClient
    _database_client: DatabaseProxy
    _container_client: ContainerProxy

    def __init__(
        self, vector_store_schema_config: VectorStoreSchemaConfig, **kwargs: Any
    ) -> None:
        super().__init__(
            vector_store_schema_config=vector_store_schema_config, **kwargs
        )

    def connect(self, **kwargs: Any) -> Any:
        """Connect to CosmosDB vector storage."""
        connection_string = kwargs.get("connection_string")
        if connection_string:
            self._cosmos_client = CosmosClient.from_connection_string(connection_string)
        else:
            url = kwargs.get("url")
            if not url:
                msg = "Either connection_string or url must be provided."
                raise ValueError(msg)
            self._cosmos_client = CosmosClient(
                url=url, credential=DefaultAzureCredential()
            )

        database_name = kwargs.get("database_name")
        if database_name is None:
            msg = "Database name must be provided."
            raise ValueError(msg)
        self._database_name = database_name
        if self.index_name is None:
            msg = "Index name is empty or not provided."
            raise ValueError(msg)
        self._container_name = self.index_name

        self.vector_size = self.vector_size
        self._create_database()
        self._create_container()

    def _create_database(self) -> None:
        """Create the database if it doesn't exist."""
        self._cosmos_client.create_database_if_not_exists(id=self._database_name)
        self._database_client = self._cosmos_client.get_database_client(
            self._database_name
        )

    def _delete_database(self) -> None:
        """Delete the database if it exists."""
        if self._database_exists():
            self._cosmos_client.delete_database(self._database_name)

    def _database_exists(self) -> bool:
        """Check if the database exists."""
        existing_database_names = [
            database["id"] for database in self._cosmos_client.list_databases()
        ]
        return self._database_name in existing_database_names

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
                id=self._container_name,
                partition_key=partition_key,
                indexing_policy=indexing_policy,
                vector_embedding_policy=vector_embedding_policy,
            )
        except CosmosHttpResponseError:
            # If diskANN fails (likely in emulator), retry without vector indexes
            indexing_policy.pop("vectorIndexes", None)

            # Create the container with compatible indexing policy
            self._database_client.create_container_if_not_exists(
                id=self._container_name,
                partition_key=partition_key,
                indexing_policy=indexing_policy,
                vector_embedding_policy=vector_embedding_policy,
            )

        self._container_client = self._database_client.get_container_client(
            self._container_name
        )

    def _delete_container(self) -> None:
        """Delete the vector store container in the database if it exists."""
        if self._container_exists():
            self._database_client.delete_container(self._container_name)

    def _container_exists(self) -> bool:
        """Check if the container name exists in the database."""
        existing_container_names = [
            container["id"] for container in self._database_client.list_containers()
        ]
        return self._container_name in existing_container_names

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into CosmosDB."""
        # Create a CosmosDB container on overwrite
        if overwrite:
            self._delete_container()
            self._create_container()

        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        # Upload documents to CosmosDB
        for doc in documents:
            if doc.vector is not None:
                print("Document to store:")  # noqa: T201
                print(doc)  # noqa: T201
                doc_json = {
                    self.id_field: doc.id,
                    self.vector_field: doc.vector,
                    self.text_field: doc.text,
                    self.attributes_field: json.dumps(doc.attributes),
                }
                print("Storing document in CosmosDB:")  # noqa: T201
                print(doc_json)  # noqa: T201
                self._container_client.upsert_item(doc_json)

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        try:
            query = f"SELECT TOP {k} c.{self.id_field}, c.{self.text_field}, c.{self.vector_field}, c.{self.attributes_field}, VectorDistance(c.{self.vector_field}, @embedding) AS SimilarityScore FROM c ORDER BY VectorDistance(c.{self.vector_field}, @embedding)"  # noqa: S608
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
            query = f"SELECT c.{self.id_field}, c.{self.text_field}, c.{self.vector_field}, c.{self.attributes_field} FROM c"  # noqa: S608
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
                    text=item.get(self.text_field, ""),
                    vector=item.get(self.vector_field, []),
                    attributes=(json.loads(item.get(self.attributes_field, "{}"))),
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

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by a list of ids."""
        if include_ids is None or len(include_ids) == 0:
            self.query_filter = None
        else:
            if isinstance(include_ids[0], str):
                id_filter = ", ".join([f"'{id}'" for id in include_ids])
            else:
                id_filter = ", ".join([str(id) for id in include_ids])
            self.query_filter = (
                f"SELECT * FROM c WHERE c.{self.id_field} IN ({id_filter})"  # noqa: S608
            )
        return self.query_filter

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        item = self._container_client.read_item(item=id, partition_key=id)
        return VectorStoreDocument(
            id=item.get(self.id_field, ""),
            vector=item.get(self.vector_field, []),
            text=item.get(self.text_field, ""),
            attributes=(json.loads(item.get(self.attributes_field, "{}"))),
        )

    def clear(self) -> None:
        """Clear the vector store."""
        self._delete_container()
        self._delete_database()
