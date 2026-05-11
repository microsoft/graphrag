# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure CosmosDB key-value Storage implementation.

This module provides a simple key-value store on top of Cosmos DB for
non-tabular data: pipeline state (context.json, stats.json), GraphML
snapshots, and LLM cache entries.

Tabular data (DataFrames / parquet) should use CosmosTableProvider instead.
"""

import contextlib
import json
import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential

from graphrag_storage.storage import (
    Storage,
    get_timestamp_formatted_with_local_tz,
)

logger = logging.getLogger(__name__)


class AzureCosmosStorage(Storage):
    """Key-value storage backed by Azure Cosmos DB.

    Each item is stored as ``{"id": key, "body": <parsed JSON or string>}``.
    The partition key is ``/id``, so every read/write is a single-partition
    point operation.

    For namespace isolation (e.g. update-run delta/previous), ``child()``
    creates a new instance that prefixes all keys with ``{namespace}/``.
    """

    _cosmos_client: CosmosClient
    _database_client: DatabaseProxy | None
    _container_client: ContainerProxy | None
    _database_name: str
    _container_name: str
    _encoding: str
    _namespace: str

    def __init__(
        self,
        database_name: str,
        container_name: str,
        connection_string: str | None = None,
        account_url: str | None = None,
        encoding: str = "utf-8",
        namespace: str = "",
        **kwargs: Any,
    ) -> None:
        """Create a CosmosDB key-value storage instance."""
        logger.info("Creating CosmosDB key-value storage")
        if not database_name:
            msg = "CosmosDB Storage requires 'database_name'."
            raise ValueError(msg)

        if connection_string is not None and account_url is not None:
            msg = "Specify either 'connection_string' or 'account_url', not both."
            raise ValueError(msg)

        if connection_string:
            self._cosmos_client = CosmosClient.from_connection_string(connection_string)
        elif account_url:
            self._cosmos_client = CosmosClient(
                url=account_url,
                credential=DefaultAzureCredential(),
            )
        else:
            msg = "CosmosDB Storage requires 'connection_string' or 'account_url'."
            raise ValueError(msg)

        self._encoding = encoding
        self._database_name = database_name
        self._connection_string = connection_string
        self._cosmosdb_account_url = account_url
        self._container_name = container_name
        self._namespace = namespace
        self._database_client = None
        self._container_client = None

        self._create_database()
        self._create_container()

    # ------------------------------------------------------------------
    # Internal DB / container management
    # ------------------------------------------------------------------

    def _create_database(self) -> None:
        self._database_client = self._cosmos_client.create_database_if_not_exists(
            id=self._database_name
        )

    def _create_container(self) -> None:
        partition_key = PartitionKey(path="/id", kind="Hash")
        if self._database_client:
            self._container_client = (
                self._database_client.create_container_if_not_exists(
                    id=self._container_name,
                    partition_key=partition_key,
                )
            )

    def _namespaced_key(self, key: str) -> str:
        """Prefix *key* with the current namespace (if any).

        Uses ``:`` as separator because Cosmos DB document ids cannot
        contain ``/`` (it is interpreted as a path separator in the REST API).
        """
        return f"{self._namespace}:{key}" if self._namespace else key

    # ------------------------------------------------------------------
    # Storage interface
    # ------------------------------------------------------------------

    def find(self, file_pattern: re.Pattern[str]) -> Iterator[str]:
        """Find documents whose id matches *file_pattern*."""
        if not self._container_client:
            return

        query = "SELECT c.id FROM c WHERE RegexMatch(c.id, @pattern)"
        parameters: list[dict[str, Any]] = [
            {"name": "@pattern", "value": file_pattern.pattern},
        ]
        try:
            items = list(
                self._container_client.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                )
            )
            for item in items:
                if file_pattern.search(item["id"]):
                    yield item["id"]
        except Exception:  # noqa: BLE001
            logger.warning(
                "Error searching Cosmos DB for pattern %s", file_pattern.pattern
            )

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Get the value for *key*.

        Returns the JSON-decoded body as a string.  If *as_bytes* is True,
        returns UTF-8 encoded bytes of the JSON body.
        """
        if not self._container_client:
            return None
        namespaced = self._namespaced_key(key)
        try:
            item = self._container_client.read_item(
                item=namespaced, partition_key=namespaced
            )
            body = item.get("body")
            result = json.dumps(body) if not isinstance(body, str) else body
        except CosmosResourceNotFoundError:
            return None
        except Exception:
            logger.exception("Error reading item %s", namespaced)
            return None
        else:
            if as_bytes:
                return result.encode(encoding or self._encoding)
            return result

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Store *value* under *key*.

        *value* should be a JSON string. It is parsed and stored under the
        ``body`` field so that Cosmos indexes it as structured data.
        """
        if not self._container_client:
            msg = "Container not initialized."
            raise ValueError(msg)
        namespaced = self._namespaced_key(key)
        try:
            # Parse JSON strings so the body is queryable; store others as-is.
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    parsed = value
            elif isinstance(value, bytes):
                parsed = value.decode(encoding or self._encoding)
            else:
                parsed = value
            cosmosdb_item = {"id": namespaced, "body": parsed}
            self._container_client.upsert_item(body=cosmosdb_item)
        except Exception:
            logger.exception("Error writing item %s", namespaced)

    async def has(self, key: str) -> bool:
        """Return True if *key* exists."""
        if not self._container_client:
            return False
        namespaced = self._namespaced_key(key)
        try:
            self._container_client.read_item(item=namespaced, partition_key=namespaced)
        except CosmosResourceNotFoundError:
            return False
        except Exception:
            logger.exception("Error checking item %s", namespaced)
            return False
        else:
            return True

    async def delete(self, key: str) -> None:
        """Delete *key*."""
        if not self._container_client:
            return
        namespaced = self._namespaced_key(key)
        try:
            self._container_client.delete_item(
                item=namespaced, partition_key=namespaced
            )
        except CosmosResourceNotFoundError:
            return
        except Exception:
            logger.exception("Error deleting item %s", namespaced)

    async def clear(self) -> None:
        """Delete all items in the current namespace.

        If no namespace is set, deletes the entire container and recreates it.
        """
        if not self._container_client or not self._database_client:
            return

        if not self._namespace:
            # Root storage: drop and recreate the container.
            self._database_client.delete_container(self._container_client)
            self._container_client = None
            self._create_container()
        else:
            # Namespaced: delete items matching the namespace prefix.
            query = "SELECT c.id FROM c WHERE STARTSWITH(c.id, @prefix)"
            parameters: list[dict[str, Any]] = [
                {"name": "@prefix", "value": f"{self._namespace}:"},
            ]
            items = list(
                self._container_client.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                )
            )
            for item in items:
                with contextlib.suppress(CosmosResourceNotFoundError):
                    self._container_client.delete_item(
                        item=item["id"], partition_key=item["id"]
                    )

    def child(self, name: str | None) -> "AzureCosmosStorage":
        """Create a child storage with an extended namespace prefix.

        Uses ``:`` as the namespace separator (``/`` is illegal in Cosmos IDs).
        """
        if name is None:
            return self
        child_ns = f"{self._namespace}:{name}" if self._namespace else name
        return AzureCosmosStorage(
            database_name=self._database_name,
            container_name=self._container_name,
            connection_string=self._connection_string,
            account_url=self._cosmosdb_account_url,
            encoding=self._encoding,
            namespace=child_ns,
        )

    def keys(self) -> list[str]:
        """List all keys in the current namespace."""
        if not self._container_client:
            return []
        if self._namespace:
            query = "SELECT c.id FROM c WHERE STARTSWITH(c.id, @prefix)"
            parameters: list[dict[str, Any]] = [
                {"name": "@prefix", "value": f"{self._namespace}:"},
            ]
            items = list(
                self._container_client.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                )
            )
            prefix_len = len(self._namespace) + 1  # +1 for ':'
            return [item["id"][prefix_len:] for item in items]

        items = list(
            self._container_client.query_items(
                query="SELECT c.id FROM c",
                enable_cross_partition_query=True,
            )
        )
        return [item["id"] for item in items]

    async def get_creation_date(self, key: str) -> str:
        """Get the creation date for *key* from the Cosmos ``_ts`` field."""
        if not self._container_client:
            return ""
        namespaced = self._namespaced_key(key)
        try:
            item = self._container_client.read_item(
                item=namespaced, partition_key=namespaced
            )
            return get_timestamp_formatted_with_local_tz(
                datetime.fromtimestamp(item["_ts"], tz=timezone.utc)
            )
        except Exception:  # noqa: BLE001
            logger.warning("Error getting creation date for %s", namespaced)
            return ""
