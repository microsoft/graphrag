 #Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure CosmosDB Storage implementation of PipelineStorage."""

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from datashaper import Progress

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

        log.info(
            "creating cosmosdb storage with account: %s and database: %s",
            self._cosmosdb_account_name,
            self._database_name,
        )
        self.create_database()
    
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
    
    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get the value for the given key."""

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Set the value for the given key."""
    
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