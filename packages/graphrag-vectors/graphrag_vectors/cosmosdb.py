# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the CosmosDB vector store implementation."""

from typing import Any

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential

from graphrag_vectors.filtering import (
    AndExpr,
    Condition,
    FilterExpr,
    NotExpr,
    Operator,
    OrExpr,
)
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
            container["id"]
            for container in self._database_client.list_containers()
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

    def insert(self, document: VectorStoreDocument) -> None:
        """Insert a single document into CosmosDB."""
        self._prepare_document(document)
        if document.vector is not None:
            doc_json: dict[str, Any] = {
                self.id_field: document.id,
                self.vector_field: document.vector,
                self.create_date_field: document.create_date,
                self.update_date_field: document.update_date,
            }
            # Add additional fields if they exist in the document data
            if document.data:
                for field_name in self.fields:
                    if field_name in document.data:
                        doc_json[field_name] = document.data[field_name]
            self._container_client.upsert_item(doc_json)

    def _compile_filter(self, expr: FilterExpr) -> str:
        """Compile a FilterExpr into a CosmosDB SQL WHERE clause.

        All field references are prefixed with 'c.' for Cosmos SQL.
        """
        match expr:
            case Condition():
                return self._compile_condition(expr)
            case AndExpr():
                parts = [self._compile_filter(e) for e in expr.and_]
                return " AND ".join(f"({p})" for p in parts)
            case OrExpr():
                parts = [self._compile_filter(e) for e in expr.or_]
                return " OR ".join(f"({p})" for p in parts)
            case NotExpr():
                inner = self._compile_filter(expr.not_)
                return f"NOT ({inner})"
            case _:
                msg = f"Unsupported filter expression type: {type(expr)}"
                raise ValueError(msg)

    def _compile_condition(self, cond: Condition) -> str:
        """Compile a single Condition to CosmosDB SQL syntax."""
        field = f"c.{cond.field}"
        value = cond.value

        def quote(v: Any) -> str:
            return f"'{v}'" if isinstance(v, str) else str(v)

        match cond.operator:
            case Operator.eq:
                return f"{field} = {quote(value)}"
            case Operator.ne:
                return f"{field} != {quote(value)}"
            case Operator.gt:
                return f"{field} > {quote(value)}"
            case Operator.gte:
                return f"{field} >= {quote(value)}"
            case Operator.lt:
                return f"{field} < {quote(value)}"
            case Operator.lte:
                return f"{field} <= {quote(value)}"
            case Operator.in_:
                items = ", ".join(quote(v) for v in value)
                return f"{field} IN ({items})"
            case Operator.not_in:
                items = ", ".join(quote(v) for v in value)
                return f"{field} NOT IN ({items})"
            case Operator.contains:
                return f"CONTAINS({field}, '{value}')"
            case Operator.startswith:
                return f"STARTSWITH({field}, '{value}')"
            case Operator.endswith:
                return f"ENDSWITH({field}, '{value}')"
            case Operator.exists:
                return (
                    f"IS_DEFINED({field})"
                    if value
                    else f"NOT IS_DEFINED({field})"
                )
            case _:
                msg = f"Unsupported operator for CosmosDB: {cond.operator}"
                raise ValueError(msg)

    def _extract_data(
        self, doc: dict[str, Any], select: list[str] | None = None
    ) -> dict[str, Any]:
        """Extract additional field data from a document response."""
        fields_to_extract = (
            select if select is not None else list(self.fields.keys())
        )
        return {
            field_name: doc[field_name]
            for field_name in fields_to_extract
            if field_name in doc
        }

    def similarity_search_by_vector(
        self,
        query_embedding: list[float],
        k: int = 10,
        select: list[str] | None = None,
        filters: FilterExpr | None = None,
        include_vectors: bool = True,
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        # Build field selection for query based on select parameter
        fields_to_select = (
            select if select is not None else list(self.fields.keys())
        )
        field_selections = ", ".join(
            [f"c.{field}" for field in fields_to_select]
        )
        if field_selections:
            field_selections = ", " + field_selections
        # Always include timestamps
        field_selections = (
            f", c.{self.create_date_field}, c.{self.update_date_field}"
            f"{field_selections}"
        )

        # Optionally include vector
        vector_select = f", c.{self.vector_field}" if include_vectors else ""

        # Build WHERE clause from filters
        where_clause = ""
        if filters is not None:
            where_clause = f" WHERE {self._compile_filter(filters)}"

        try:
            query = (
                f"SELECT TOP {k} c.{self.id_field}{vector_select}"
                f"{field_selections},"
                f" VectorDistance(c.{self.vector_field}, @embedding)"
                f" AS SimilarityScore FROM c{where_clause}"
                f" ORDER BY VectorDistance(c.{self.vector_field}, @embedding)"
            )  # noqa: S608
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
            query = (
                f"SELECT c.{self.id_field}, c.{self.vector_field}"
                f"{field_selections} FROM c{where_clause}"
            )  # noqa: S608
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
                items,
                key=lambda x: x.get("SimilarityScore", 0.0),
                reverse=True,
            )[:k]

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=item.get(self.id_field, ""),
                    vector=item.get(self.vector_field, [])
                    if include_vectors
                    else None,
                    data=self._extract_data(item, select),
                    create_date=item.get(self.create_date_field),
                    update_date=item.get(self.update_date_field),
                ),
                score=item.get("SimilarityScore", 0.0),
            )
            for item in items
        ]

    def search_by_id(
        self,
        id: str,
        select: list[str] | None = None,
        include_vectors: bool = True,
    ) -> VectorStoreDocument:
        """Search for a document by id."""
        if self._container_client is None:
            msg = "Container client is not initialized."
            raise ValueError(msg)

        item = self._container_client.read_item(item=id, partition_key=id)
        return VectorStoreDocument(
            id=item[self.id_field],
            vector=item.get(self.vector_field, [])
            if include_vectors
            else None,
            data=self._extract_data(item, select),
            create_date=item.get(self.create_date_field),
            update_date=item.get(self.update_date_field),
        )

    def count(self) -> int:
        """Return the total number of documents in the store."""
        query = "SELECT VALUE COUNT(1) FROM c"
        result = list(
            self._container_client.query_items(
                query=query,
                enable_cross_partition_query=True,
            )
        )
        return result[0] if result else 0

    def remove(self, ids: list[str]) -> None:
        """Remove documents by their IDs."""
        for doc_id in ids:
            self._container_client.delete_item(
                item=doc_id, partition_key=doc_id
            )

    def update(self, document: VectorStoreDocument) -> None:
        """Update an existing document in the store."""
        self._prepare_update(document)

        # Read the existing document
        existing = self._container_client.read_item(
            item=document.id, partition_key=document.id
        )

        # Set update_date
        existing[self.update_date_field] = document.update_date

        # Update vector if provided
        if document.vector is not None:
            existing[self.vector_field] = document.vector

        # Update data fields if provided
        if document.data:
            for field_name in self.fields:
                if field_name in document.data:
                    existing[field_name] = document.data[field_name]

        # Upsert the updated document
        self._container_client.upsert_item(existing)

    def clear(self) -> None:
        """Clear the vector store."""
        self._delete_container()
        self._delete_database()
