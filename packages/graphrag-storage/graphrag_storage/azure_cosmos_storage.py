# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure CosmosDB Storage implementation of PipelineStorage."""

import json
import logging
import re
from collections.abc import Iterator
from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import Any

import pandas as pd
from azure.cosmos import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential
from graphrag.logger.progress import Progress

from graphrag_storage.storage import (
    Storage,
    get_timestamp_formatted_with_local_tz,
)

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZE = 100


class AzureCosmosStorage(Storage):
    """The CosmosDB-Storage Implementation."""

    _cosmos_client: CosmosClient
    _database_client: DatabaseProxy | None
    _container_client: ContainerProxy | None
    _cosmosdb_account_url: str | None
    _connection_string: str | None
    _database_name: str
    _container_name: str
    _encoding: str
    _no_id_prefixes: set[str]

    def __init__(
        self,
        database_name: str,
        container_name: str,
        connection_string: str | None = None,
        account_url: str | None = None,
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> None:
        """Create a CosmosDB storage instance."""
        logger.info("Creating cosmosdb storage")
        database_name = database_name
        if not database_name:
            msg = "CosmosDB Storage requires a base_dir to be specified. This is used as the database name."
            logger.error(msg)
            raise ValueError(msg)

        if connection_string is not None and account_url is not None:
            msg = "CosmosDB Storage requires either a connection_string or cosmosdb_account_url to be specified, not both."
            logger.error(msg)
            raise ValueError(msg)

        if connection_string:
            self._cosmos_client = CosmosClient.from_connection_string(connection_string)
        elif account_url:
            self._cosmos_client = CosmosClient(
                url=account_url,
                credential=DefaultAzureCredential(),
            )
        else:
            msg = "CosmosDB Storage requires either a connection_string or cosmosdb_account_url to be specified."
            logger.error(msg)
            raise ValueError(msg)

        self._encoding = encoding
        self._database_name = database_name
        self._connection_string = connection_string
        self._cosmosdb_account_url = account_url
        self._container_name = container_name
        self._cosmosdb_account_name = (
            account_url.split("//")[1].split(".")[0] if account_url else None
        )
        self._no_id_prefixes = set()
        logger.debug(
            "Creating cosmosdb storage with account [%s] and database [%s] and container [%s]",
            self._cosmosdb_account_name,
            self._database_name,
            self._container_name,
        )
        self._create_database()
        self._create_container()

    def _create_database(self) -> None:
        """Create the database if it doesn't exist."""
        self._database_client = self._cosmos_client.create_database_if_not_exists(
            id=self._database_name
        )

    def _delete_database(self) -> None:
        """Delete the database if it exists."""
        if self._database_client:
            self._database_client = self._cosmos_client.delete_database(
                self._database_client
            )
        self._container_client = None

    def _create_container(self) -> None:
        """Create a container for the current container name if it doesn't exist."""
        partition_key = PartitionKey(path="/id", kind="Hash")
        if self._database_client:
            self._container_client = (
                self._database_client.create_container_if_not_exists(
                    id=self._container_name,
                    partition_key=partition_key,
                )
            )

    def _delete_container(self) -> None:
        """Delete the container with the current container name if it exists."""
        if self._database_client and self._container_client:
            self._container_client = self._database_client.delete_container(
                self._container_client
            )

    def find(
        self,
        file_pattern: re.Pattern[str],
    ) -> Iterator[str]:
        """Find documents in a Cosmos DB container using a file pattern regex.

        Params:
            file_pattern: The file pattern to use.

        Returns
        -------
            An iterator of document IDs and their corresponding regex matches.
        """
        logger.info(
            "Search container [%s] for documents matching [%s]",
            self._container_name,
            file_pattern.pattern,
        )
        if not self._database_client or not self._container_client:
            return

        try:
            query = "SELECT * FROM c WHERE RegexMatch(c.id, @pattern)"
            parameters: list[dict[str, Any]] = [
                {"name": "@pattern", "value": file_pattern.pattern}
            ]

            items = self._query_all_items(
                self._container_client,
                query=query,
                parameters=parameters,
            )
            logger.debug("All items: %s", [item["id"] for item in items])
            num_loaded = 0
            num_total = len(items)
            if num_total == 0:
                return
            num_filtered = 0
            for item in items:
                match = file_pattern.search(item["id"])
                if match:
                    yield item["id"]
                    num_loaded += 1
                else:
                    num_filtered += 1

            progress_status = _create_progress_status(
                num_loaded, num_filtered, num_total
            )
            logger.debug(
                "Progress: %s (%d/%d completed)",
                progress_status.description,
                progress_status.completed_items,
                progress_status.total_items,
            )
        except Exception:  # noqa: BLE001
            logger.warning(
                "An error occurred while searching for documents in Cosmos DB."
            )

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Fetch all items in a container that match the given key."""
        try:
            if not self._database_client or not self._container_client:
                return None

            if as_bytes:
                prefix = self._get_prefix(key)
                query = f"SELECT * FROM c WHERE STARTSWITH(c.id, '{prefix}:')"  # noqa: S608
                items_list = self._query_all_items(
                    self._container_client,
                    query=query,
                )

                logger.info("Cosmos load prefix=%s count=%d", prefix, len(items_list))

                if not items_list:
                    logger.warning("No items found for prefix %s (key=%s)", prefix, key)
                    return None

                for item in items_list:
                    item["id"] = item["id"].split(":", 1)[1]

                items_json_str = json.dumps(items_list)
                items_df = pd.read_json(
                    StringIO(items_json_str), orient="records", lines=False
                )

                if prefix == "entities":
                    # Always preserve the Cosmos suffix for debugging/migrations
                    items_df["cosmos_id"] = items_df["id"]
                    items_df["id"] = items_df["id"].astype(
                        str
                    )  # Only restore pipeline UUID id if we actually have it

                    if "human_readable_id" in items_df.columns:
                        # Fill any NaN values before converting to int
                        items_df["human_readable_id"] = (
                            items_df["human_readable_id"]
                            .fillna(items_df["id"])
                            .astype(int)
                        )
                    else:
                        # Fresh run case: extract_graph entities may not have entity_id yet
                        # Keep id as the suffix (stable_key/index) for now.
                        logger.info(
                            "Entities loaded without entity_id; leaving id as cosmos suffix."
                        )

                if items_df.empty:
                    logger.warning(
                        "No rows returned for prefix %s (key=%s)", prefix, key
                    )
                    return None
                return items_df.to_parquet()
            item = self._container_client.read_item(item=key, partition_key=key)
            item_body = item.get("body")
            return json.dumps(item_body)
        except Exception:
            logger.exception("Error reading item %s", key)
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Write an item to Cosmos DB. If the value is bytes, we assume it's a parquet file and we write each row as a separate item with id formatted as {prefix}:{stable_key_or_index}."""
        if not self._database_client or not self._container_client:
            error_msg = "Database or container not initialized. Cannot write item."
            raise ValueError(error_msg)
        try:
            if isinstance(value, bytes):
                prefix = self._get_prefix(key)
                value_df = pd.read_parquet(BytesIO(value))

                # Decide once per dataframe
                df_has_id = "id" in value_df.columns

                # IMPORTANT: if we now have ids, undo the earlier "no id" marking
                if df_has_id:
                    self._no_id_prefixes.discard(prefix)
                else:
                    self._no_id_prefixes.add(prefix)

                cosmosdb_item_list = json.loads(
                    value_df.to_json(orient="records", lines=False, force_ascii=False)
                )

                for index, cosmosdb_item in enumerate(cosmosdb_item_list):
                    if prefix == "entities":
                        # Stable key for Cosmos identity
                        stable_key = cosmosdb_item.get("human_readable_id", index)
                        cosmos_id = f"{prefix}:{stable_key}"

                        # If the pipeline provided a final UUID, store it separately
                        if "id" in cosmosdb_item:
                            cosmosdb_item["entity_id"] = cosmosdb_item["id"]

                        # Cosmos identity must be stable and NEVER change
                        cosmosdb_item["id"] = cosmos_id

                    else:
                        # Original behavior for non-entity prefixes
                        if df_has_id:
                            cosmosdb_item["id"] = f"{prefix}:{cosmosdb_item['id']}"
                        else:
                            cosmosdb_item["id"] = f"{prefix}:{index}"

                    self._container_client.upsert_item(body=cosmosdb_item)
            else:
                cosmosdb_item = {"id": key, "body": json.loads(value)}
                self._container_client.upsert_item(body=cosmosdb_item)

        except Exception:
            logger.exception("Error writing item %s", key)

    async def has(self, key: str) -> bool:
        """Check if the contents of the given filename key exist in the cosmosdb storage."""
        if not self._database_client or not self._container_client:
            return False
        if ".parquet" in key:
            prefix = self._get_prefix(key)
            count = self._query_count(
                self._container_client,
                query_filter=f"STARTSWITH(c.id, '{prefix}:')",
            )
            return count > 0
        count = self._query_count(
            self._container_client,
            query_filter=f"c.id = '{key}'",
        )
        return count >= 1

    def _query_all_items(
        self,
        container_client: ContainerProxy,
        query: str,
        parameters: list[dict[str, Any]] | None = None,
        page_size: int = _DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        """Fetch all items from a Cosmos DB query using pagination.

        This avoids the pitfalls of calling list() on the full pager, which can
        time out or return incomplete results for large result sets.
        """
        results: list[dict[str, Any]] = []
        query_kwargs: dict[str, Any] = {
            "query": query,
            "enable_cross_partition_query": True,
            "max_item_count": page_size,
        }
        if parameters:
            query_kwargs["parameters"] = parameters

        pager = container_client.query_items(**query_kwargs).by_page()
        for page in pager:
            results.extend(page)
        return results

    def _query_count(
        self,
        container_client: ContainerProxy,
        query_filter: str,
        parameters: list[dict[str, Any]] | None = None,
    ) -> int:
        """Return the count of items matching a filter, without fetching them all.

        Parameters
        ----------
        query_filter:
            The WHERE clause (without 'WHERE'), e.g. "STARTSWITH(c.id, 'entities:')".
        """
        count_query = f"SELECT VALUE COUNT(1) FROM c WHERE {query_filter}"  # noqa: S608
        query_kwargs: dict[str, Any] = {
            "query": count_query,
            "enable_cross_partition_query": True,
        }
        if parameters:
            query_kwargs["parameters"] = parameters

        results = list(container_client.query_items(**query_kwargs))
        return int(results[0]) if results else 0  # type: ignore[arg-type]

    async def delete(self, key: str) -> None:
        """Delete all cosmosdb items belonging to the given filename key."""
        if not self._database_client or not self._container_client:
            return
        try:
            if ".parquet" in key:
                prefix = self._get_prefix(key)
                query = f"SELECT * FROM c WHERE STARTSWITH(c.id, '{prefix}:')"  # noqa: S608
                items = self._query_all_items(
                    self._container_client,
                    query=query,
                )
                for item in items:
                    self._container_client.delete_item(
                        item=item["id"], partition_key=item["id"]
                    )
            else:
                self._container_client.delete_item(item=key, partition_key=key)
        except CosmosResourceNotFoundError:
            return
        except Exception:
            logger.exception("Error deleting item %s", key)

    async def clear(self) -> None:
        """Clear all contents from storage.

        # This currently deletes the database, including all containers and data within it.
        # TODO: We should decide what granularity of deletion is the ideal behavior (e.g. delete all items within a container, delete the current container, delete the current database)
        """
        self._delete_database()

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        msg = "CosmosDB storage does yet not support listing keys."
        raise NotImplementedError(msg)

    def child(self, name: str | None) -> "Storage":
        """Create a child storage instance."""
        return self

    def _get_prefix(self, key: str) -> str:
        """Get the prefix of the filename key."""
        return key.split(".")[0]

    async def get_creation_date(self, key: str) -> str:
        """Get a value from the cache."""
        try:
            if not self._database_client or not self._container_client:
                return ""
            item = self._container_client.read_item(item=key, partition_key=key)
            return get_timestamp_formatted_with_local_tz(
                datetime.fromtimestamp(item["_ts"], tz=timezone.utc)
            )

        except Exception:  # noqa: BLE001
            logger.warning("Error getting key %s", key)
            return ""


def _create_progress_status(
    num_loaded: int, num_filtered: int, num_total: int
) -> Progress:
    return Progress(
        total_items=num_total,
        completed_items=num_loaded + num_filtered,
        description=f"{num_loaded} files loaded ({num_filtered} filtered)",
    )
