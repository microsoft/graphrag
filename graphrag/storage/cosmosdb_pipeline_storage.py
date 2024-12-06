# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Azure CosmosDB Storage implementation of PipelineStorage."""

import json
import logging
import re
from collections.abc import Iterator
from io import BytesIO, StringIO
from typing import Any

import pandas as pd
from azure.cosmos import CosmosClient
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential
from datashaper import Progress

from graphrag.logging.base import ProgressReporter
from graphrag.storage.pipeline_storage import PipelineStorage

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
        encoding: str = "utf-8",
        current_container: str | None = None,
    ):
        """Initialize the CosmosDB Storage."""
        if connection_string:
            self._cosmos_client = CosmosClient.from_connection_string(connection_string)
        else:
            if cosmosdb_account_url is None:
                msg = (
                    "Either connection_string or cosmosdb_account_url must be provided."
                )
                raise ValueError(msg)

            self._cosmos_client = CosmosClient(
                url=cosmosdb_account_url,
                credential=DefaultAzureCredential(),
            )

        self._encoding = encoding
        self._database_name = database_name
        self._connection_string = connection_string
        self._cosmosdb_account_url = cosmosdb_account_url
        self._current_container = current_container
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
        self._create_database()
        if self._current_container:
            self._create_container()

    def _create_database(self) -> None:
        """Create the database if it doesn't exist."""
        self._cosmos_client.create_database_if_not_exists(id=self._database_name)

    def _delete_database(self) -> None:
        """Delete the database if it exists."""
        if self._database_exists():
            self._cosmos_client.delete_database(self._database_name)

    def _database_exists(self) -> bool:
        """Check if the database exists."""
        database_names = [
            database["id"] for database in self._cosmos_client.list_databases()
        ]
        return self._database_name in database_names

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
            return all(
                re.match(value, item.get(key, "")) for key, value in file_filter.items()
            )

        try:
            container_client = self._database_client.get_container_client(
                str(self._current_container)
            )
            query = "SELECT * FROM c WHERE CONTAINS(c.id, @pattern)"
            parameters: list[dict[str, Any]] = [
                {"name": "@pattern", "value": file_pattern.pattern}
            ]
            if file_filter:
                for key, value in file_filter.items():
                    query += f" AND c.{key} = @{key}"
                    parameters.append({"name": f"@{key}", "value": value})
            items = container_client.query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            )
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
            log.exception(
                "An error occurred while searching for documents in Cosmos DB."
            )

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        """Fetch all cosmosdb items belonging to the given filename key."""
        try:
            if self._current_container:
                container_client = self._database_client.get_container_client(
                    self._current_container
                )
                prefix = self._get_prefix(key)
                query = f"SELECT * FROM c WHERE STARTSWITH(c.id, '{prefix}:')"  # noqa: S608
                queried_items = container_client.query_items(
                    query=query, enable_cross_partition_query=True
                )
                items_list = list(queried_items)
                for item in items_list:
                    item["id"] = item["id"].split(":")[1]

                items_json_str = json.dumps(items_list)
                if as_bytes:
                    items_df = pd.read_json(
                        StringIO(items_json_str), orient="records", lines=False
                    )
                    return items_df.to_parquet()
                return items_json_str
        except Exception:
            log.exception("Error reading item %s", key)
            return None
        else:
            return None

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        """Insert the contents of a file into cosmosdb for the given filename key. For optimization, the file is destructured such that each row is a unique cosmosdb item."""
        try:
            if self._current_container:
                container_client = self._database_client.get_container_client(
                    self._current_container
                )
                prefix = self._get_prefix(key)
                if isinstance(value, bytes):
                    value_df = pd.read_parquet(BytesIO(value))
                    value_json = value_df.to_json(
                        orient="records", lines=False, force_ascii=False
                    )
                    if value_json is None:
                        log.exception("Error converting output %s to json", key)
                    else:
                        cosmosdb_item_list = json.loads(value_json)
                        for cosmosdb_item in cosmosdb_item_list:
                            prefixed_id = f"{prefix}:{cosmosdb_item['id']}"
                            cosmosdb_item["id"] = prefixed_id
                            container_client.upsert_item(body=cosmosdb_item)
                else:
                    cosmosdb_item_list = json.loads(value)
                    for cosmosdb_item in cosmosdb_item_list:
                        prefixed_id = f"{prefix}:{cosmosdb_item['id']}"
                        cosmosdb_item["id"] = prefixed_id
                        container_client.upsert_item(body=cosmosdb_item)

        except Exception:
            log.exception("Error writing item %s", key)

    async def has(self, key: str) -> bool:
        """Check if the contents of the given filename key exist in the cosmosdb storage."""
        if self._current_container:
            container_client = self._database_client.get_container_client(
                self._current_container
            )
            prefix = self._get_prefix(key)
            query = f"SELECT * FROM c WHERE STARTSWITH(c.id, '{prefix}:')"  # noqa: S608
            queried_items = container_client.query_items(
                    query=query, enable_cross_partition_query=True
            )
            return len(list(queried_items)) > 0
        return False

    async def delete(self, key: str) -> None:
        """Delete all comsmosdb items belonging to the given filename key."""
        if self._current_container:
            container_client = self._database_client.get_container_client(
                self._current_container
            )
            prefix = self._get_prefix(key)
            query = f"SELECT * FROM c WHERE STARTSWITH(c.id, '{prefix}:')"  # noqa: S608
            queried_items = container_client.query_items(
                    query=query, enable_cross_partition_query=True
            )
            for item in queried_items:
                container_client.delete_item(item=item["id"], partition_key=item["id"])

    # Function currently deletes all items within the current container, then deletes the container itself.
    # TODO: Decide the granularity of deletion (e.g. delete all items within the current container, delete the current container, delete the current database)
    async def clear(self) -> None:
        """Clear the cosmosdb storage."""
        if self._current_container:
            container_client = self._database_client.get_container_client(
                self._current_container
            )
            for item in container_client.read_all_items():
                item_id = item["id"]
                container_client.delete_item(item=item_id, partition_key=item_id)
            self._delete_container()

    def keys(self) -> list[str]:
        """Return the keys in the storage."""
        msg = "CosmosDB storage does yet not support listing keys."
        raise NotImplementedError(msg)

    def child(self, name: str | None) -> PipelineStorage:
        """Create a child storage instance."""
        return self
    
    def _get_prefix(self, key: str) -> str:
        """Get the prefix of the filename key."""
        return key.split(".")[0]

    def _create_container(self) -> None:
        """Create a container for the current container name if it doesn't exist."""
        if self._current_container:
            partition_key = PartitionKey(path="/id", kind="Hash")
            self._database_client.create_container_if_not_exists(
                id=self._current_container,
                partition_key=partition_key,
            )

    def _delete_container(self) -> None:
        """Delete the container with the current container name if it exists."""
        if self._container_exists() and self._current_container:
            self._database_client.delete_container(self._current_container)

    def _container_exists(self) -> bool:
        """Check if the container with the current container name exists."""
        container_names = [
            container["id"] for container in self._database_client.list_containers()
        ]
        return self._current_container in container_names


# TODO remove this helper function and have the factory instantiate the class directly
# once the new config system is in place and will enforce the correct types/existence of certain fields
def create_cosmosdb_storage(**kwargs: Any) -> PipelineStorage:
    """Create a CosmosDB storage instance."""
    log.info("Creating cosmosdb storage")
    cosmosdb_account_url = kwargs.get("cosmosdb_account_url")
    connection_string = kwargs.get("connection_string")
    base_dir = kwargs.get("base_dir")
    container_name = kwargs.get("container_name")
    if not base_dir:
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
