 #Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure CosmosDB Storage implementation of PipelineStorage."""

import logging
import re
from collections.abc import Iterator
from typing import Any

from azure.cosmos import CosmosClient
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential

from graphrag.logging import ProgressReporter

from .pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)

class CosmosDBPipelineStorage(PipelineStorage):
    """The CosmosDB-Storage Implementation."""

    _cosmosdb_account_url: str
    _primary_key: str | None
    _database_name: str
    _current_container: str | None
    _encoding: str

    def __init__(
        self,
        cosmosdb_account_url: str,
        primary_key: str | None,
        database_name: str,
        encoding: str | None = None,
        _current_container: str | None = None,
    ):
        """Initialize the CosmosDB-Storage."""
        if not cosmosdb_account_url:
            msg = "cosmosdb_account_url is required"
            raise ValueError(msg)
        
        if primary_key:
            self._cosmos_client = CosmosClient(
                url=cosmosdb_account_url,
                credential=primary_key,
            )
        else:
            self._cosmos_client = CosmosClient(
                url=cosmosdb_account_url,
                credential=DefaultAzureCredential(),
            )

        self._encoding = encoding or "utf-8"
        self._database_name = database_name
        self._primary_key = primary_key
        self._cosmosdb_account_url = cosmosdb_account_url
        self._current_container = _current_container or None
        self._cosmosdb_account_name = cosmosdb_account_url.split("//")[1].split(".")[0]
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
        """Find files in the cosmosdb storage using a file pattern, as well as a custom filter function."""
        msg = "CosmosDB storage does yet not support finding files."
        raise NotImplementedError(msg)
    
    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get a file in the database for the given key."""

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set a file in the database for the given key."""

    async def has(self, key: str) -> bool:
        """Check if the given file exists in the cosmosdb storage."""
        return True

    async def delete(self, key: str) -> None:
        """Delete the given file from the cosmosdb storage."""

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
            self._cosmosdb_account_url,
            self._primary_key,
            self._database_name,
            name,
            self._encoding,
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