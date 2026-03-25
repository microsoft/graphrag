# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

import asyncio
from typing import Any

from graphrag.index.operations.finalize_entities import finalize_entities
from graphrag.index.operations.finalize_relationships import finalize_relationships
from graphrag_storage.tables.table import Table


class FakeTable(Table):
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = list(rows or [])
        self._index = 0
        self.written: list[dict[str, Any]] = []

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self) -> dict[str, Any]:
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        row = dict(self._rows[self._index])
        self._index += 1
        return row

    async def length(self) -> int:
        return len(self._rows)

    async def has(self, row_id: str) -> bool:
        return any(r.get("id") == row_id for r in self._rows)

    async def write(self, row: dict[str, Any]) -> None:
        self.written.append(row)

    async def close(self) -> None:
        return None


def test_finalize_entities_fills_temporal_evidence_defaults():
    table = FakeTable(
        [
            {
                "title": "A",
                "type": "PERSON",
                "description": "desc",
                "frequency": 1,
                "text_unit_ids": ["tu1", "tu2"],
            }
        ]
    )

    asyncio.run(finalize_entities(table, {"A": 2}))

    row = table.written[0]
    assert row["evidence_count"] == 2
    assert row["first_seen_text_unit_id"] == "tu1"
    assert row["last_seen_text_unit_id"] == "tu2"


def test_finalize_relationships_fills_temporal_evidence_defaults():
    table = FakeTable(
        [
            {
                "source": "A",
                "target": "B",
                "description": "desc",
                "weight": 1.0,
                "text_unit_ids": ["tu1", "tu2", "tu3"],
            }
        ]
    )

    asyncio.run(finalize_relationships(table, {"A": 1, "B": 1}))

    row = table.written[0]
    assert row["evidence_count"] == 3
    assert row["first_seen_text_unit_id"] == "tu1"
    assert row["last_seen_text_unit_id"] == "tu3"
