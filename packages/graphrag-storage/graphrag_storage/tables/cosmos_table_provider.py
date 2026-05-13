# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Cosmos DB native table provider implementation.

Stores each DataFrame row as a Cosmos document, eliminating the
parquet serialization round-trip used by ParquetTableProvider.

Container schema
----------------
Partition key : /namespace
Document id   : {table_name}:{row_key}

Every document carries two internal fields used for routing:
    namespace  - partition key, set by child() hierarchy
    table_name - discriminator for per-table queries

All queries target a single namespace partition (no cross-partition fan-out).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import pandas as pd
from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.partition_key import PartitionKey
from azure.identity.aio import DefaultAzureCredential

from graphrag_storage.tables.cosmos_table import (
    CosmosTable,
    _strip_cosmos_metadata,
)
from graphrag_storage.tables.table import RowTransformer, Table
from graphrag_storage.tables.table_provider import TableProvider

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZE = 100

_DEFAULT_BATCH_SIZE = 50
_MAX_BATCH_SIZE = 100


class CosmosTableProvider(TableProvider):
    """TableProvider backed by Azure Cosmos DB (NoSQL API, async SDK).

    Each table is stored as a set of documents within a single container,
    discriminated by the ``table_name`` field. Namespace isolation (used
    by the update pipeline's delta/previous split) is achieved via the
    ``/namespace`` partition key.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        *,
        connection_string: str | None = None,
        account_url: str | None = None,
        database_name: str | None = None,
        container_name: str | None = None,
        namespace: str = "",
        legacy_container: str | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        # Allow pre-built internals for child() and testing.
        _cosmos_client: CosmosClient | None = None,
        _container: ContainerProxy | None = None,
        _legacy_container: ContainerProxy | None = None,
        **kwargs: Any,
    ) -> None:
        self._batch_size = min(max(batch_size, 1), _MAX_BATCH_SIZE)

        if _container is not None:
            # Fast path: child() or test injection.
            self._cosmos_client = _cosmos_client
            self._container = _container
            self._legacy_container = _legacy_container
            self._namespace = namespace
            self._owns_client = False
            return

        # Normal construction from config values.
        if not database_name:
            msg = "CosmosTableProvider requires 'database_name'."
            raise ValueError(msg)
        if not container_name:
            msg = "CosmosTableProvider requires 'container_name'."
            raise ValueError(msg)
        if connection_string and account_url:
            msg = "Specify either 'connection_string' or 'account_url', not both."
            raise ValueError(msg)
        if not connection_string and not account_url:
            msg = "CosmosTableProvider requires 'connection_string' or 'account_url'."
            raise ValueError(msg)

        if connection_string:
            self._cosmos_client = CosmosClient.from_connection_string(connection_string)
        else:
            self._cosmos_client = CosmosClient(
                url=account_url,  # type: ignore[arg-type]
                credential=DefaultAzureCredential(),
            )

        self._namespace = namespace
        self._owns_client = True

        # Containers are created lazily on first use via _ensure_container().
        self._database_name = database_name
        self._container_name = container_name
        self._legacy_container_name = legacy_container
        self._container: ContainerProxy | None = None  # type: ignore[assignment]
        self._legacy_container: ContainerProxy | None = None
        self._container_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Lazy initialization (async work we can't do in __init__)
    # ------------------------------------------------------------------

    async def _ensure_container(self) -> ContainerProxy:
        """Return the container proxy, creating DB / container on first call."""
        if self._container is not None:
            return self._container

        async with self._container_lock:
            if self._container is not None:
                return self._container

            db: DatabaseProxy = await self._cosmos_client.create_database_if_not_exists(  # type: ignore[union-attr]
                id=self._database_name
            )
            self._container = await db.create_container_if_not_exists(
                id=self._container_name,
                partition_key=PartitionKey(path="/namespace", kind="Hash"),
            )

            if self._legacy_container_name:
                self._legacy_container = db.get_container_client(
                    self._legacy_container_name
                )

        return self._container

    # ------------------------------------------------------------------
    # TableProvider interface
    # ------------------------------------------------------------------

    async def read_dataframe(self, table_name: str) -> pd.DataFrame:
        """Read all rows for *table_name* within the current namespace."""
        container = await self._ensure_container()

        query = "SELECT * FROM c WHERE c.table_name = @table_name"
        parameters: list[dict[str, Any]] = [
            {"name": "@table_name", "value": table_name},
        ]

        docs: list[dict[str, Any]] = []
        async for page in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=self._namespace,
            max_item_count=_DEFAULT_PAGE_SIZE,
        ).by_page():
            async for doc in page:
                docs.append(_strip_cosmos_metadata(doc))  # noqa: PERF401

        if docs:
            return pd.DataFrame(docs)

        # ---- Legacy fallback (optional) --------------------------------
        if self._legacy_container is not None:
            df = await self._read_legacy_table(table_name)
            if df is not None and not df.empty:
                logger.warning(
                    "Reading '%s' from legacy container — run "
                    "'graphrag migrate-cosmos' to complete migration.",
                    table_name,
                )
                return df

        msg = f"Table '{table_name}' not found in namespace '{self._namespace}'."
        raise ValueError(msg)

    async def write_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """Write *df* as documents, replacing any existing rows for this table."""
        container = await self._ensure_container()

        # Delete existing documents for this table in the namespace.
        await self._delete_table(container, table_name)

        records = json.loads(
            df.to_json(orient="records", lines=False, force_ascii=False)
        )
        docs = []
        for index, row in enumerate(records):
            row_key = row.pop("id", index)
            doc = {
                "id": f"{table_name}:{row_key}",
                "namespace": self._namespace,
                "table_name": table_name,
                **row,
            }
            # Preserve the pipeline's id value so it round-trips.
            doc["row_id"] = row_key
            docs.append(doc)

        await _batch_upsert(container, docs, self._namespace, self._batch_size)

    async def has(self, table_name: str) -> bool:
        """Check whether any documents exist for *table_name*."""
        container = await self._ensure_container()
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.table_name = @table_name"
        parameters: list[dict[str, Any]] = [
            {"name": "@table_name", "value": table_name},
        ]
        results: list[Any] = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=self._namespace,
        ):
            results.append(item)  # noqa: PERF401
        if results and results[0] > 0:
            return True

        # Fallback: check legacy container.
        if self._legacy_container is not None:
            return await self._legacy_table_exists(table_name)
        return False

    def list(self) -> list[str]:
        """List all table names in the current namespace.

        Note: this method is synchronous in the ABC. We run a sync wrapper
        over the async query. Callers that need pure-async should use
        ``list_async()`` instead.
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an async context — create a task via a helper.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, self._list_async()).result()
        return asyncio.run(self._list_async())

    async def _list_async(self) -> list[str]:
        """Async implementation of list()."""
        container = await self._ensure_container()
        query = "SELECT DISTINCT VALUE c.table_name FROM c"
        names: list[Any] = []
        async for item in container.query_items(
            query=query,
            partition_key=self._namespace,
        ):
            names.append(item)  # noqa: PERF401
        return names

    def open(
        self,
        table_name: str,
        transformer: RowTransformer | None = None,
        truncate: bool = True,
    ) -> Table:
        """Open a table for streaming row-by-row access."""
        return _LazyCosmosTable(
            provider=self,
            table_name=table_name,
            transformer=transformer,
            truncate=truncate,
            batch_size=self._batch_size,
        )

    # ------------------------------------------------------------------
    # child() — namespace isolation
    # ------------------------------------------------------------------

    def child(self, name: str | None) -> CosmosTableProvider:
        """Create a child provider with an extended namespace."""
        if name is None:
            return self
        child_ns = f"{self._namespace}/{name}" if self._namespace else name
        return CosmosTableProvider(
            _cosmos_client=self._cosmos_client,
            _container=self._container,
            _legacy_container=self._legacy_container,
            namespace=child_ns,
            batch_size=self._batch_size,
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying Cosmos client if we own it."""
        if self._owns_client and self._cosmos_client is not None:
            await self._cosmos_client.close()
            self._cosmos_client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _delete_table(self, container: ContainerProxy, table_name: str) -> None:
        """Delete all documents for a table in the current namespace."""
        query = "SELECT c.id FROM c WHERE c.table_name = @table_name"
        parameters: list[dict[str, Any]] = [
            {"name": "@table_name", "value": table_name},
        ]
        ids: list[str] = [
            doc["id"]
            async for page in container.query_items(
                query=query,
                parameters=parameters,
                partition_key=self._namespace,
            ).by_page()
            async for doc in page
        ]
        if ids:
            await _batch_delete(container, ids, self._namespace, self._batch_size)

    # ------------------------------------------------------------------
    # Legacy fallback reads
    # ------------------------------------------------------------------

    async def _read_legacy_table(self, table_name: str) -> pd.DataFrame | None:
        """Read from the old AzureCosmosStorage container (partition key /id).

        Legacy documents have id = "{prefix}:{key}" and no namespace/table_name
        fields.  Entity documents have the pipeline id renamed to entity_id.
        """
        if self._legacy_container is None:
            return None

        prefix = table_name
        query = "SELECT * FROM c WHERE STARTSWITH(c.id, @prefix)"
        parameters: list[dict[str, Any]] = [
            {"name": "@prefix", "value": f"{prefix}:"},
        ]

        docs: list[dict[str, Any]] = []
        async for page in self._legacy_container.query_items(
            query=query,
            parameters=parameters,
            max_item_count=_DEFAULT_PAGE_SIZE,
        ).by_page():
            async for doc in page:
                # Strip the "{prefix}:" from the id.
                raw_id = doc.get("id", "")
                if ":" in raw_id:
                    doc["id"] = raw_id.split(":", 1)[1]

                # Reverse entity-specific hacks.
                if table_name == "entities" and "entity_id" in doc:
                    doc["id"] = doc.pop("entity_id")

                docs.append(_strip_cosmos_metadata(doc))

        if not docs:
            return None
        return pd.DataFrame(docs)

    async def _legacy_table_exists(self, table_name: str) -> bool:
        """Check if the legacy container has documents for this table prefix."""
        if self._legacy_container is None:
            return False
        prefix = table_name
        query = "SELECT VALUE COUNT(1) FROM c WHERE STARTSWITH(c.id, @prefix)"
        parameters: list[dict[str, Any]] = [
            {"name": "@prefix", "value": f"{prefix}:"},
        ]
        results: list[Any] = []
        async for item in self._legacy_container.query_items(
            query=query,
            parameters=parameters,
        ):
            results.append(item)  # noqa: PERF401
        return bool(results and results[0] > 0)


async def _batch_upsert(
    container: ContainerProxy,
    docs: list[dict[str, Any]],
    partition_key: str,
    batch_size: int,
) -> None:
    """Upsert *docs* using transactional batches with single-upsert fallback.

    Documents are split into chunks of *batch_size* (max 100). Each chunk is
    sent as a transactional batch.  If a batch fails (e.g. payload too large),
    the chunk is retried as individual upserts so that partial progress is
    never lost.
    """
    from azure.cosmos.exceptions import CosmosBatchOperationError

    for start in range(0, len(docs), batch_size):
        chunk = docs[start : start + batch_size]
        try:
            ops = [("upsert", (doc,)) for doc in chunk]
            await container.execute_item_batch(ops, partition_key=partition_key)
        except CosmosBatchOperationError:
            logger.warning(
                "Transactional batch failed for %d docs at offset %d; "
                "falling back to individual upserts.",
                len(chunk),
                start,
            )
            for doc in chunk:
                await container.upsert_item(body=doc)


async def _batch_delete(
    container: ContainerProxy,
    item_ids: list[str],
    partition_key: str,
    batch_size: int,
) -> None:
    """Delete items by ID using transactional batches with single-delete fallback.

    Same chunking and fallback strategy as :func:`_batch_upsert`.
    """
    from azure.cosmos.exceptions import CosmosBatchOperationError

    for start in range(0, len(item_ids), batch_size):
        chunk = item_ids[start : start + batch_size]
        try:
            ops = [("delete", (item_id,)) for item_id in chunk]
            await container.execute_item_batch(ops, partition_key=partition_key)
        except CosmosBatchOperationError:
            logger.warning(
                "Transactional batch delete failed for %d items at offset %d; "
                "falling back to individual deletes.",
                len(chunk),
                start,
            )
            for item_id in chunk:
                await container.delete_item(item=item_id, partition_key=partition_key)


class _LazyCosmosTable(Table):
    """Wrapper that lazily resolves the container for CosmosTable.

    open() is synchronous but _ensure_container() is async, so we defer
    container resolution to the first async operation.
    """

    def __init__(
        self,
        provider: CosmosTableProvider,
        table_name: str,
        transformer: RowTransformer | None,
        truncate: bool,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        self._provider = provider
        self._table_name = table_name
        self._transformer = transformer
        self._truncate = truncate
        self._batch_size = batch_size
        self._inner: CosmosTable | None = None

    async def _ensure_inner(self) -> CosmosTable:
        if self._inner is None:
            container = await self._provider._ensure_container()  # noqa: SLF001
            self._inner = CosmosTable(
                container=container,
                table_name=self._table_name,
                namespace=self._provider._namespace,  # noqa: SLF001
                transformer=self._transformer,
                truncate=self._truncate,
                batch_size=self._batch_size,
            )
        return self._inner

    def __aiter__(self):
        return self._aiter_impl()

    async def _aiter_impl(self):
        inner = await self._ensure_inner()
        async for row in inner:
            yield row

    async def length(self) -> int:
        inner = await self._ensure_inner()
        return await inner.length()

    async def has(self, row_id: str) -> bool:
        inner = await self._ensure_inner()
        return await inner.has(row_id)

    async def write(self, row: dict[str, Any]) -> None:
        inner = await self._ensure_inner()
        await inner.write(row)

    async def close(self) -> None:
        if self._inner is not None:
            await self._inner.close()
