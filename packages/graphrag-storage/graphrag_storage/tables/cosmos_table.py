# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Cosmos DB implementation of the Table abstraction for streaming row access."""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from graphrag_storage.tables.table import RowTransformer, Table

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from azure.cosmos.aio import ContainerProxy

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZE = 100
_DEFAULT_BATCH_SIZE = 50


def _identity(row: dict[str, Any]) -> Any:
    """Return row unchanged (default transformer)."""
    return row


def _apply_transformer(transformer: RowTransformer, row: dict[str, Any]) -> Any:
    """Apply transformer, handling both callables and classes (e.g. Pydantic models)."""
    if inspect.isclass(transformer):
        return transformer(**row)
    return transformer(row)


# Cosmos system properties to strip from returned rows.
_COSMOS_SYSTEM_KEYS = frozenset({
    "_rid",
    "_self",
    "_etag",
    "_attachments",
    "_ts",
    "namespace",
    "table_name",
})


def _strip_cosmos_metadata(doc: dict[str, Any]) -> dict[str, Any]:
    """Remove Cosmos system properties and restore original id."""
    result = {k: v for k, v in doc.items() if k not in _COSMOS_SYSTEM_KEYS}
    # Restore the pipeline's original id from row_id if present.
    if "row_id" in result:
        result["id"] = result.pop("row_id")
    return result


class CosmosTable(Table):
    """Streaming table interface backed by Cosmos DB.

    Reads page through query_items() using the async SDK, yielding rows
    one at a time.  Writes accumulate in memory and are bulk-upserted on
    close().
    """

    def __init__(
        self,
        container: ContainerProxy,
        table_name: str,
        namespace: str,
        transformer: RowTransformer | None = None,
        truncate: bool = True,
        page_size: int = _DEFAULT_PAGE_SIZE,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        """Initialise with a Cosmos container and table/namespace identifiers."""
        self._container = container
        self._table_name = table_name
        self._namespace = namespace
        self._transformer = transformer or _identity
        self._truncate = truncate
        self._page_size = page_size
        self._batch_size = batch_size
        self._write_rows: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def __aiter__(self) -> AsyncIterator[Any]:
        """Iterate rows asynchronously."""
        return self._aiter_impl()

    async def _aiter_impl(self) -> AsyncIterator[Any]:
        """Page through Cosmos query results, yielding transformed rows."""
        query = "SELECT * FROM c WHERE c.table_name = @table_name"
        parameters: list[dict[str, Any]] = [
            {"name": "@table_name", "value": self._table_name},
        ]
        async for page in self._container.query_items(
            query=query,
            parameters=parameters,
            partition_key=self._namespace,
            max_item_count=self._page_size,
        ).by_page():
            async for doc in page:
                row = _strip_cosmos_metadata(doc)
                yield _apply_transformer(self._transformer, row)

    async def length(self) -> int:
        """Return the number of rows in the table (single-partition COUNT)."""
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.table_name = @table_name"
        parameters: list[dict[str, Any]] = [
            {"name": "@table_name", "value": self._table_name},
        ]
        results: list[Any] = []
        async for item in self._container.query_items(
            query=query,
            parameters=parameters,
            partition_key=self._namespace,
        ):
            results.append(item)  # noqa: PERF401
        return int(results[0]) if results else 0

    async def has(self, row_id: str) -> bool:
        """Check if a row with the given ID exists (point-read)."""
        cosmos_id = f"{self._table_name}:{row_id}"
        try:
            await self._container.read_item(
                item=cosmos_id, partition_key=self._namespace
            )
        except CosmosResourceNotFoundError:
            return False
        else:
            return True

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def write(self, row: dict[str, Any]) -> None:
        """Accumulate a row for batch upsert on close()."""
        self._write_rows.append(row)

    async def close(self) -> None:
        """Flush accumulated rows to Cosmos DB.

        If truncate=True, existing documents for this table in the namespace
        are deleted before writing.
        """
        if self._truncate and self._write_rows:
            await self._delete_table_docs()

        docs = []
        for index, row in enumerate(self._write_rows):
            doc = dict(row)
            row_key = doc.pop("id", index)
            doc["id"] = f"{self._table_name}:{row_key}"
            doc["namespace"] = self._namespace
            doc["table_name"] = self._table_name
            doc["row_id"] = row_key
            docs.append(doc)

        if docs:
            from graphrag_storage.tables.cosmos_table_provider import (
                _batch_upsert,
            )

            await _batch_upsert(
                self._container, docs, self._namespace, self._batch_size
            )

        self._write_rows = []

    async def _delete_table_docs(self) -> None:
        """Delete all documents for this table in the current namespace."""
        query = "SELECT c.id FROM c WHERE c.table_name = @table_name"
        parameters: list[dict[str, Any]] = [
            {"name": "@table_name", "value": self._table_name},
        ]
        async for page in self._container.query_items(
            query=query,
            parameters=parameters,
            partition_key=self._namespace,
        ).by_page():
            async for doc in page:
                await self._container.delete_item(
                    item=doc["id"], partition_key=self._namespace
                )
