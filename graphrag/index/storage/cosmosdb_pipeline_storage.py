 #Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure CosmosDB Storage implementation of PipelineStorage."""

import json
import logging
import re
from collections.abc import Iterator
from typing import Any

from azure.cosmos import CosmosClient
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential
from datashaper import Progress

from graphrag.logging import ProgressReporter

from .pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)

class CosmosDBPipelineStorage(PipelineStorage):
    """The CosmosDB-Storage Implementation."""

    _cosmosdb_account_url: str | None
    _connection_string: str | None
    _database_name: str
    _current_container: str | None
    _encoding: str

    def __init__(
        self,
        cosmosdb_account_url: str | None,
        connection_string: str | None,
        database_name: str,
        encoding: str | None = None,
        current_container: str | None = None,
    ):
        """Initialize the CosmosDB-Storage."""
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
                credential=DefaultAzureCredential(),
            )

        self._encoding = encoding or "utf-8"
        self._database_name = database_name
        self._connection_string = connection_string
        self._cosmosdb_account_url = cosmosdb_account_url
        self._current_container = current_container or None
        self._cosmosdb_account_name = (
            cosmosdb_account_url.split("//")[1].split(".")[0]
            if cosmosdb_account_url
            else None
        )
        self._database_client = self._cosmos_client.get_database_client(
            self._database_name
        )

        log.info(
            "creating cosmosdb storage with account: %s and database: %s",
            self._cosmosdb_account_name,
            self._database_name,
        )
        self.create_database()
        if self._current_container is not None:
            self.create_container()
    
    def create_database(self) -> None:
        """Create the database if it doesn't exist."""
        if not self.database_exists():
            database_name = self._database_name
            database_names = [
                database["id"] for database in self._cosmos_client.list_databases()
            ]
            if database_name not in database_names:
                self._cosmos_client.create_database(database_name)

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
    
    def find(
        self,
        file_pattern: re.Pattern[str],
        base_dir: str | None = None,
        progress: ProgressReporter | None = None,
        file_filter: dict[str, Any] | None = None,
        max_count=-1,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """Find documents in a Cosmos DB container using a file pattern and custom filter function.

        Params:
            base_dir: The name of the base directory (not used in Cosmos DB context).
            file_pattern: The file pattern to use.
            file_filter: A dictionary of key-value pairs to filter the documents.
            max_count: The maximum number of documents to return. If -1, all documents are returned.

        Returns
        -------
            An iterator of document IDs and their corresponding regex matches.
        """
        base_dir = base_dir or ""

        log.info(
            "search container %s for documents matching %s",
            self._current_container,
            file_pattern.pattern,
        )

        def item_filter(item: dict[str, Any]) -> bool:
            if file_filter is None:
                return True
            return all(re.match(value, item.get(key, "")) for key, value in file_filter.items())

        try:
            database_client = self._database_client
            container_client = database_client.get_container_client(str(self._current_container))
            query = "SELECT * FROM c WHERE CONTAINS(c.id, @pattern)"
            parameters: list[dict[str, Any]] = [{"name": "@pattern", "value": file_pattern.pattern}]
            if file_filter:
                for key, value in file_filter.items():
                    query += f" AND c.{key} = @{key}"
                    parameters.append({"name": f"@{key}", "value": value})
            items = container_client.query_items(query=query, parameters=parameters, enable_cross_partition_query=True)
            num_loaded = 0
            num_total = len(list(items))
            num_filtered = 0
            for item in items:
                match = file_pattern.match(item["id"])
                if match:
                    group = match.groupdict()
                    if item_filter(group):
                        yield (item["id"], group)
                        num_loaded += 1
                        if max_count > 0 and num_loaded >= max_count:
                            break
                    else:
                        num_filtered += 1
                else:
                    num_filtered += 1
                if progress is not None:
                    progress(
                        _create_progress_status(num_loaded, num_filtered, num_total)
                    )
        except Exception:
            log.exception("An error occurred while searching for documents in Cosmos DB.")

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get a file in the database for the given key."""
        try:
            database_client = self._database_client
            if self._current_container is not None:
                container_client = database_client.get_container_client(
                    self._current_container
                )
                item = container_client.read_item(item=key, partition_key=key)
                item_body = item.get("body")
                if as_bytes:
                    coding = encoding or "utf-8"
                    return json.dumps(item_body).encode(coding)
                return json.dumps(item_body)
        except Exception:
            log.exception("Error reading item %s", key)
            return None
        else:
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set a file in the database for the given key."""
        try:
            database_client = self._database_client
            if self._current_container is not None:
                container_client = database_client.get_container_client(
                    self._current_container
                )
                if isinstance(value, bytes):
                    msg = "Parquet table emitter not supported for CosmosDB storage."
                    log.exception(msg)
                else:
                    cosmos_db_item = {
                        "id": key,
                        "body": json.loads(value)
                    }
                    container_client.upsert_item(body=cosmos_db_item)
        except Exception:
            log.exception("Error writing item %s", key)

    async def has(self, key: str) -> bool:
        """Check if the given file exists in the cosmosdb storage."""
        database_client = self._database_client
        if self._current_container is not None:
            container_client = database_client.get_container_client(
                self._current_container
            )
            item_names = [
                item["id"]
                for item in container_client.read_all_items()
            ]
            return key in item_names
        return False

    async def delete(self, key: str) -> None:
        """Delete the given file from the cosmosdb storage."""
        database_client = self._database_client
        if self._current_container is not None:
            container_client = database_client.get_container_client(
                self._current_container
            )
            container_client.delete_item(item=key, partition_key=key)

    async def clear(self) -> None:
        """Clear the cosmosdb storage."""

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        msg = "CosmosDB storage does yet not support listing keys."
        raise NotImplementedError(msg)
    
    def child(self, name: str | None) -> "PipelineStorage":
        """Create a child storage instance."""
        if name is None:
            return self
        return CosmosDBPipelineStorage(
            cosmosdb_account_url=self._cosmosdb_account_url,
            connection_string=self._connection_string,
            database_name=self._database_name,
            encoding=self._encoding,
            current_container=name,
        )
    
    def create_container(self) -> None:
        """Create a container for the current container name if it doesn't exist."""
        database_client = self._database_client
        if not self.container_exists() and self._current_container is not None:
            container_names = [
                container["id"]
                for container in database_client.list_containers()
            ]
            if self._current_container not in container_names:
                partition_key = PartitionKey(path="/id", kind="Hash")
                database_client.create_container(
                    id=self._current_container,
                    partition_key=partition_key,
                )
            
        
    def delete_container(self) -> None:
        """Delete the container with the current container name if it exists."""
        database_client = self._database_client
        if self.container_exists() and self._current_container is not None:
            database_client.delete_container(self._current_container)

    def container_exists(self) -> bool:
        """Check if the container with the current container name exists."""
        database_client = self._database_client
        container_names = [
            container["id"]
            for container in database_client.list_containers()
        ]
        return self._current_container in container_names
    
def create_cosmosdb_storage(
    cosmosdb_account_url: str | None,
    connection_string: str | None,
    base_dir: str,
    container_name: str | None,
) -> PipelineStorage:
    """Create a CosmosDB storage instance."""
    log.info("Creating cosmosdb storage")
    if base_dir is None:
        msg = "No base_dir provided for database name"
        raise ValueError(msg)
    if connection_string is None and cosmosdb_account_url is None:
        msg = "No cosmosdb account url provided"
        raise ValueError(msg)
    return CosmosDBPipelineStorage(
        cosmosdb_account_url=cosmosdb_account_url,
        connection_string=connection_string,
        database_name=base_dir,
        current_container=container_name,
    )

def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )
