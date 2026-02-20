# Copyright (C) 2026 Microsoft
# Licensed under the MIT License

"""Tests for the finalize_graph streaming functions.

Covers _build_degree_map, finalize_entities, finalize_relationships,
and the orchestrating finalize_graph function.
"""

from typing import Any

import pytest
from graphrag.data_model.schemas import (
    ENTITIES_FINAL_COLUMNS,
    RELATIONSHIPS_FINAL_COLUMNS,
)
from graphrag.index.operations.finalize_entities import finalize_entities
from graphrag.index.operations.finalize_relationships import (
    finalize_relationships,
)
from graphrag.index.workflows.finalize_graph import (
    _build_degree_map,
    finalize_graph,
)
from graphrag_storage.tables.table import Table


class FakeTable(Table):
    """In-memory table that supports async iteration and write collection.

    Rows passed to write() are collected in ``written`` for assertions.
    Each call to ``__aiter__`` resets the read cursor so the table can
    be iterated multiple times, matching the real CSVTable behavior
    under truncate mode.
    """

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = list(rows or [])
        self._index = 0
        self.written: list[dict[str, Any]] = []

    def __aiter__(self):
        """Return an async iterator over the seed rows."""
        self._index = 0
        return self

    async def __anext__(self) -> dict[str, Any]:
        """Yield the next row or stop."""
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        row = dict(self._rows[self._index])
        self._index += 1
        return row

    async def length(self) -> int:
        """Return number of seed rows."""
        return len(self._rows)

    async def has(self, row_id: str) -> bool:
        """Check if a row with the given ID exists in seed rows."""
        return any(r.get("id") == row_id for r in self._rows)

    async def write(self, row: dict[str, Any]) -> None:
        """Collect written rows for test assertions."""
        self.written.append(row)

    async def close(self) -> None:
        """No-op."""


def _make_entity_row(
    title: str,
    entity_type: str = "ENTITY",
    description: str = "",
    frequency: int = 1,
) -> dict[str, Any]:
    """Build a minimal entity row matching pre-finalization shape."""
    return {
        "title": title,
        "type": entity_type,
        "description": description,
        "frequency": frequency,
        "text_unit_ids": ["tu1"],
    }


def _make_relationship_row(
    source: str,
    target: str,
    weight: float = 1.0,
    description: str = "",
) -> dict[str, Any]:
    """Build a minimal relationship row matching pre-finalization shape."""
    return {
        "source": source,
        "target": target,
        "weight": weight,
        "description": description,
        "text_unit_ids": ["tu1"],
    }


class TestBuildDegreeMap:
    """Tests for the streaming _build_degree_map helper."""

    async def test_simple_triangle(self):
        """Three nodes forming a triangle should each have degree 2."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("B", "C"),
            _make_relationship_row("A", "C"),
        ])
        result = await _build_degree_map(table)
        assert result == {"A": 2, "B": 2, "C": 2}

    async def test_star_topology(self):
        """Hub connected to four leaves should have degree 4; leaves degree 1."""
        table = FakeTable([
            _make_relationship_row("hub", "a"),
            _make_relationship_row("hub", "b"),
            _make_relationship_row("hub", "c"),
            _make_relationship_row("hub", "d"),
        ])
        result = await _build_degree_map(table)
        assert result["hub"] == 4
        for leaf in ("a", "b", "c", "d"):
            assert result[leaf] == 1

    async def test_duplicate_edges_deduplicated(self):
        """Duplicate (A, B) edges should be counted only once."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("A", "B"),
        ])
        result = await _build_degree_map(table)
        assert result == {"A": 1, "B": 1}

    async def test_reversed_duplicate_edges_deduplicated(self):
        """(A, B) and (B, A) are the same undirected edge."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("B", "A"),
        ])
        result = await _build_degree_map(table)
        assert result == {"A": 1, "B": 1}

    async def test_empty_table(self):
        """Empty relationship table should produce empty degree map."""
        table = FakeTable([])
        result = await _build_degree_map(table)
        assert result == {}

    async def test_single_edge(self):
        """One edge yields degree 1 for both endpoints."""
        table = FakeTable([_make_relationship_row("X", "Y")])
        result = await _build_degree_map(table)
        assert result == {"X": 1, "Y": 1}

    async def test_disconnected_components(self):
        """Two separate components computed correctly."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("C", "D"),
        ])
        result = await _build_degree_map(table)
        assert result == {"A": 1, "B": 1, "C": 1, "D": 1}


class TestFinalizeEntities:
    """Tests for stream-finalize entity rows."""

    async def test_enriches_with_degree(self):
        """Entities should receive degree from the degree map."""
        table = FakeTable([
            _make_entity_row("A"),
            _make_entity_row("B"),
        ])
        degree_map = {"A": 3, "B": 1}
        await finalize_entities(table, degree_map)

        assert len(table.written) == 2
        assert table.written[0]["degree"] == 3
        assert table.written[1]["degree"] == 1

    async def test_missing_degree_defaults_to_zero(self):
        """Entity not in degree map should get degree 0."""
        table = FakeTable([_make_entity_row("UNKNOWN")])
        degree_map = {"A": 5}
        await finalize_entities(table, degree_map)

        assert len(table.written) == 1
        assert table.written[0]["degree"] == 0

    async def test_deduplicates_by_title(self):
        """Duplicate titles should be skipped."""
        table = FakeTable([
            _make_entity_row("A"),
            _make_entity_row("A"),
            _make_entity_row("B"),
        ])
        degree_map = {"A": 1, "B": 2}
        await finalize_entities(table, degree_map)

        assert len(table.written) == 2
        titles = [r["title"] for r in table.written]
        assert titles == ["A", "B"]

    async def test_skips_empty_title(self):
        """Rows with empty or missing title should be skipped."""
        table = FakeTable([
            _make_entity_row(""),
            _make_entity_row("A"),
        ])
        degree_map = {"A": 1}
        await finalize_entities(table, degree_map)

        assert len(table.written) == 1
        assert table.written[0]["title"] == "A"

    async def test_assigns_sequential_human_readable_ids(self):
        """human_readable_id should be 0-based sequential."""
        table = FakeTable([
            _make_entity_row("A"),
            _make_entity_row("B"),
            _make_entity_row("C"),
        ])
        degree_map = {"A": 1, "B": 1, "C": 1}
        await finalize_entities(table, degree_map)

        ids = [r["human_readable_id"] for r in table.written]
        assert ids == [0, 1, 2]

    async def test_assigns_unique_ids(self):
        """Each entity should get a unique UUID id."""
        table = FakeTable([
            _make_entity_row("A"),
            _make_entity_row("B"),
        ])
        degree_map = {"A": 1, "B": 1}
        await finalize_entities(table, degree_map)

        row_ids = [r["id"] for r in table.written]
        assert len(set(row_ids)) == 2

    async def test_output_columns_match_schema(self):
        """Written rows should contain exactly the ENTITIES_FINAL_COLUMNS."""
        table = FakeTable([_make_entity_row("A")])
        degree_map = {"A": 1}
        await finalize_entities(table, degree_map)

        assert set(table.written[0].keys()) == set(ENTITIES_FINAL_COLUMNS)

    async def test_returns_sample_rows_up_to_five(self):
        """Should return at most 5 sample rows."""
        rows = [_make_entity_row(f"E{i}") for i in range(8)]
        table = FakeTable(rows)
        degree_map = {f"E{i}": 1 for i in range(8)}
        samples = await finalize_entities(table, degree_map)

        assert len(samples) == 5
        assert len(table.written) == 8

    async def test_empty_table(self):
        """Empty input should produce no output."""
        table = FakeTable([])
        degree_map = {}
        samples = await finalize_entities(table, degree_map)

        assert samples == []
        assert table.written == []


class TestFinalizeRelationships:
    """Tests for stream-finalize relationship rows."""

    async def test_enriches_with_combined_degree(self):
        """combined_degree should be sum of source and target degrees."""
        table = FakeTable([_make_relationship_row("A", "B")])
        degree_map = {"A": 3, "B": 2}
        await finalize_relationships(table, degree_map)

        assert len(table.written) == 1
        assert table.written[0]["combined_degree"] == 5

    async def test_missing_degree_defaults_to_zero(self):
        """Nodes not in degree map contribute 0 to combined_degree."""
        table = FakeTable([_make_relationship_row("X", "Y")])
        degree_map = {"X": 4}
        await finalize_relationships(table, degree_map)

        assert table.written[0]["combined_degree"] == 4

    async def test_deduplicates_by_source_target(self):
        """Duplicate (source, target) pairs should be skipped."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("A", "B"),
            _make_relationship_row("B", "C"),
        ])
        degree_map = {"A": 1, "B": 2, "C": 1}
        await finalize_relationships(table, degree_map)

        assert len(table.written) == 2
        pairs = [(r["source"], r["target"]) for r in table.written]
        assert pairs == [("A", "B"), ("B", "C")]

    async def test_reversed_pair_not_deduplicated(self):
        """(A,B) and (B,A) are treated as distinct directed edges."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("B", "A"),
        ])
        degree_map = {"A": 1, "B": 1}
        await finalize_relationships(table, degree_map)

        assert len(table.written) == 2

    async def test_assigns_sequential_human_readable_ids(self):
        """human_readable_id should be 0-based sequential."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("B", "C"),
        ])
        degree_map = {"A": 1, "B": 2, "C": 1}
        await finalize_relationships(table, degree_map)

        ids = [r["human_readable_id"] for r in table.written]
        assert ids == [0, 1]

    async def test_assigns_unique_ids(self):
        """Each relationship should get a unique UUID id."""
        table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("B", "C"),
        ])
        degree_map = {"A": 1, "B": 2, "C": 1}
        await finalize_relationships(table, degree_map)

        row_ids = [r["id"] for r in table.written]
        assert len(set(row_ids)) == 2

    async def test_output_columns_match_schema(self):
        """Written rows should contain exactly RELATIONSHIPS_FINAL_COLUMNS."""
        table = FakeTable([_make_relationship_row("A", "B")])
        degree_map = {"A": 1, "B": 1}
        await finalize_relationships(table, degree_map)

        assert set(table.written[0].keys()) == set(RELATIONSHIPS_FINAL_COLUMNS)

    async def test_returns_sample_rows_up_to_five(self):
        """Should return at most 5 sample rows."""
        rows = [_make_relationship_row(f"S{i}", f"T{i}") for i in range(8)]
        table = FakeTable(rows)
        degree_map = {f"S{i}": 1 for i in range(8)} | {f"T{i}": 1 for i in range(8)}
        samples = await finalize_relationships(table, degree_map)

        assert len(samples) == 5
        assert len(table.written) == 8

    async def test_empty_table(self):
        """Empty input should produce no output."""
        table = FakeTable([])
        degree_map = {}
        samples = await finalize_relationships(table, degree_map)

        assert samples == []
        assert table.written == []


class TestFinalizeGraph:
    """Tests for the orchestrating finalize_graph function."""

    async def test_produces_entities_and_relationships_keys(self):
        """Result dict should have 'entities' and 'relationships' keys."""
        entities_table = FakeTable([_make_entity_row("A")])
        relationships_table = FakeTable([_make_relationship_row("A", "B")])
        result = await finalize_graph(entities_table, relationships_table)

        assert "entities" in result
        assert "relationships" in result

    async def test_degree_flows_through_to_entities(self):
        """Entity degree should reflect computed edge degrees."""
        entities_table = FakeTable([
            _make_entity_row("A"),
            _make_entity_row("B"),
            _make_entity_row("C"),
        ])
        relationships_table = FakeTable([
            _make_relationship_row("A", "B"),
            _make_relationship_row("A", "C"),
        ])
        await finalize_graph(entities_table, relationships_table)

        degree_by_title = {r["title"]: r["degree"] for r in entities_table.written}
        assert degree_by_title["A"] == 2
        assert degree_by_title["B"] == 1
        assert degree_by_title["C"] == 1

    async def test_combined_degree_flows_through_to_relationships(self):
        """Relationship combined_degree should be sum of endpoint degrees."""
        entities_table = FakeTable([
            _make_entity_row("A"),
            _make_entity_row("B"),
        ])
        relationships_table = FakeTable([
            _make_relationship_row("A", "B"),
        ])
        await finalize_graph(entities_table, relationships_table)

        assert len(relationships_table.written) == 1
        assert relationships_table.written[0]["combined_degree"] == 2

    async def test_empty_graph(self):
        """Empty tables should produce empty results."""
        entities_table = FakeTable([])
        relationships_table = FakeTable([])
        result = await finalize_graph(entities_table, relationships_table)

        assert result == {"entities": [], "relationships": []}

    @pytest.mark.parametrize(
        ("entity_count", "relationship_count"),
        [
            (3, 2),
            (10, 15),
        ],
        ids=["small", "medium"],
    )
    async def test_all_rows_written(self, entity_count: int, relationship_count: int):
        """All unique entities and relationships should be written."""
        entity_rows = [_make_entity_row(f"E{i}") for i in range(entity_count)]
        relationship_rows = [
            _make_relationship_row(f"E{i}", f"E{(i + 1) % entity_count}")
            for i in range(relationship_count)
        ]
        entities_table = FakeTable(entity_rows)
        relationships_table = FakeTable(relationship_rows)

        await finalize_graph(entities_table, relationships_table)

        assert len(entities_table.written) == entity_count
        unique_rel_pairs = {(r["source"], r["target"]) for r in relationship_rows}
        assert len(relationships_table.written) == len(unique_rel_pairs)
