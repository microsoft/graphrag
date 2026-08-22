# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Tests for snapshot_graphml operation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import pandas as pd
from graphrag.index.operations.snapshot_graphml import (
    _XML_HEADER,
    snapshot_graphml,
)
from graphrag_storage import Storage

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator


class FakeStorage(Storage):
    """In-memory storage for testing."""

    def __init__(self, **kwargs: Any) -> None:
        self.data: dict[str, str] = {}

    async def set(self, key: str, value: Any, encoding: str | None = None) -> None:
        self.data[key] = value

    def find(self, file_pattern: re.Pattern[str]) -> Iterator[str]:
        yield from []

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        return self.data.get(key)

    async def has(self, key: str) -> bool:
        return key in self.data

    async def delete(self, key: str) -> None:
        self.data.pop(key, None)

    async def clear(self) -> None:
        self.data.clear()

    def child(self, name: str | None) -> FakeStorage:
        return FakeStorage()

    def keys(self) -> list[str]:
        return list(self.data.keys())

    async def get_creation_date(self, key: str) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %z")


def _make_edges(
    rows: list[tuple[str, str, float]],
) -> pd.DataFrame:
    """Build a minimal relationships DataFrame."""
    return pd.DataFrame(rows, columns=["source", "target", "weight"])


class TestSnapshotGraphml:
    """Tests for the snapshot_graphml function."""

    async def test_output_has_xml_header(self) -> None:
        """GraphML output must start with the XML declaration."""
        edges = _make_edges([("A", "B", 1.0)])
        storage = FakeStorage()
        await snapshot_graphml(edges, "graph", storage)

        content = storage.data["graph.graphml"]
        assert content.startswith(_XML_HEADER)

    async def test_output_is_valid_graphml(self) -> None:
        """Output should contain <graphml> root element."""
        edges = _make_edges([("A", "B", 1.0)])
        storage = FakeStorage()
        await snapshot_graphml(edges, "graph", storage)

        content = storage.data["graph.graphml"]
        assert "<graphml" in content
        assert "</graphml>" in content

    async def test_empty_graph(self) -> None:
        """Empty edge list should produce valid GraphML with XML header."""
        edges = _make_edges([])
        storage = FakeStorage()
        await snapshot_graphml(edges, "graph", storage)

        content = storage.data["graph.graphml"]
        assert content.startswith(_XML_HEADER)
        assert "<graphml" in content
