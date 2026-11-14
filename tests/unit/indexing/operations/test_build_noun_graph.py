# Copyright (C) 2026 Microsoft Corporation.
# Licensed under the MIT License

"""Tests for build_noun_graph edge extraction with Top-K and co-occurrence filters.

Validates that _extract_edges correctly applies max_entities_per_chunk (Top-K)
and min_co_occurrence filters to control the O(N^2) co-occurrence edge explosion
in entity-dense corpora.
"""

import pandas as pd

from graphrag.index.operations.build_noun_graph.build_noun_graph import (
    _extract_edges,
)


def _make_nodes_df(title_to_ids: dict[str, list[str]]) -> pd.DataFrame:
    """Build a nodes DataFrame from a title_to_ids mapping."""
    return pd.DataFrame(
        [
            {"title": t, "frequency": len(ids), "text_unit_ids": ids}
            for t, ids in title_to_ids.items()
        ],
        columns=["title", "frequency", "text_unit_ids"],
    )


class TestExtractEdgesDefaults:
    """Baseline behaviour with default parameters (no filtering)."""

    def test_empty_input(self):
        """Empty title_to_ids produces an empty edges DataFrame."""
        edges = _extract_edges({}, pd.DataFrame(), normalize_edge_weights=False)
        assert len(edges) == 0
        assert list(edges.columns) == ["source", "target", "weight", "text_unit_ids"]

    def test_single_entity_no_edges(self):
        """A single entity cannot form any pairs."""
        title_to_ids = {"alpha": ["tu1", "tu2"]}
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(title_to_ids, nodes, normalize_edge_weights=False)
        assert len(edges) == 0

    def test_two_entities_one_chunk(self):
        """Two entities in the same chunk produce exactly one edge."""
        title_to_ids = {"alpha": ["tu1"], "beta": ["tu1"]}
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(title_to_ids, nodes, normalize_edge_weights=False)
        assert len(edges) == 1
        assert edges.iloc[0]["weight"] == 1

    def test_co_occurrence_weight(self):
        """Weight equals the number of shared text units."""
        title_to_ids = {"alpha": ["tu1", "tu2", "tu3"], "beta": ["tu1", "tu2", "tu3"]}
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(title_to_ids, nodes, normalize_edge_weights=False)
        assert len(edges) == 1
        assert edges.iloc[0]["weight"] == 3

    def test_all_pairs_generated(self):
        """N entities in one chunk produce C(N,2) edges."""
        title_to_ids = {
            "a": ["tu1"],
            "b": ["tu1"],
            "c": ["tu1"],
            "d": ["tu1"],
        }
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(title_to_ids, nodes, normalize_edge_weights=False)
        # C(4,2) = 6
        assert len(edges) == 6


class TestMaxEntitiesPerChunk:
    """Top-K entity filtering per text unit."""

    def test_disabled_when_zero(self):
        """max_entities_per_chunk=0 keeps all entities (default)."""
        title_to_ids = {
            "a": ["tu1"],
            "b": ["tu1"],
            "c": ["tu1"],
            "d": ["tu1"],
            "e": ["tu1"],
        }
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids,
            nodes,
            normalize_edge_weights=False,
            max_entities_per_chunk=0,
        )
        # C(5,2) = 10
        assert len(edges) == 10

    def test_caps_entities_per_chunk(self):
        """Only top-K most frequent entities are paired per chunk."""
        # Frequencies: a=3, b=3, c=1, d=1, e=1  (all in tu1)
        title_to_ids = {
            "a": ["tu1", "tu2", "tu3"],
            "b": ["tu1", "tu2", "tu3"],
            "c": ["tu1"],
            "d": ["tu1"],
            "e": ["tu1"],
        }
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids,
            nodes,
            normalize_edge_weights=False,
            max_entities_per_chunk=2,
        )
        # Only a and b survive the top-2 filter → C(2,2)=1 edge
        assert len(edges) == 1
        sources_targets = set(edges.iloc[0][["source", "target"]])
        assert sources_targets == {"a", "b"}

    def test_no_effect_when_below_limit(self):
        """Top-K has no effect when chunk has fewer entities than K."""
        title_to_ids = {"a": ["tu1"], "b": ["tu1"]}
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids,
            nodes,
            normalize_edge_weights=False,
            max_entities_per_chunk=10,
        )
        assert len(edges) == 1

    def test_selects_by_global_frequency(self):
        """Top-K selection uses global frequency, not per-chunk count."""
        # In tu1: a, b, c, d all present
        # Global freq: a=5, b=4, c=1, d=1
        # Top-2 by global freq → a, b
        title_to_ids = {
            "a": ["tu1", "tu2", "tu3", "tu4", "tu5"],
            "b": ["tu1", "tu2", "tu3", "tu4"],
            "c": ["tu1"],
            "d": ["tu1"],
        }
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids,
            nodes,
            normalize_edge_weights=False,
            max_entities_per_chunk=2,
        )
        assert len(edges) == 1
        sources_targets = set(edges.iloc[0][["source", "target"]])
        assert sources_targets == {"a", "b"}

    def test_reduces_quadratic_explosion(self):
        """Top-K significantly reduces edges in dense chunks."""
        # 20 entities in one chunk: C(20,2) = 190 edges without limit
        title_to_ids = {chr(65 + i): ["tu1"] for i in range(20)}
        nodes = _make_nodes_df(title_to_ids)

        edges_all = _extract_edges(
            title_to_ids, nodes, normalize_edge_weights=False, max_entities_per_chunk=0
        )
        edges_k5 = _extract_edges(
            title_to_ids, nodes, normalize_edge_weights=False, max_entities_per_chunk=5
        )
        # C(20,2) = 190, C(5,2) = 10
        assert len(edges_all) == 190
        assert len(edges_k5) == 10


class TestMinCoOccurrence:
    """Minimum co-occurrence threshold filtering."""

    def test_default_keeps_all(self):
        """min_co_occurrence=1 keeps all edges (default)."""
        title_to_ids = {"a": ["tu1"], "b": ["tu1"]}
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids, nodes, normalize_edge_weights=False, min_co_occurrence=1
        )
        assert len(edges) == 1

    def test_filters_low_co_occurrence(self):
        """Edges appearing in fewer than min_co_occurrence chunks are removed."""
        title_to_ids = {
            "a": ["tu1", "tu2"],
            "b": ["tu1", "tu2"],
            "c": ["tu1"],
        }
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids, nodes, normalize_edge_weights=False, min_co_occurrence=2
        )
        # a-b co-occur in tu1,tu2 (weight=2) → kept
        # a-c co-occur in tu1 only (weight=1) → removed
        # b-c co-occur in tu1 only (weight=1) → removed
        assert len(edges) == 1
        assert set(edges.iloc[0][["source", "target"]]) == {"a", "b"}

    def test_removes_all_when_threshold_too_high(self):
        """All edges removed when threshold exceeds max weight."""
        title_to_ids = {"a": ["tu1"], "b": ["tu1"]}
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids, nodes, normalize_edge_weights=False, min_co_occurrence=5
        )
        assert len(edges) == 0


class TestCombinedFilters:
    """Top-K and co-occurrence filters work together."""

    def test_both_filters_applied(self):
        """Top-K limits entities, then co-occurrence filters weak edges."""
        # 6 entities in tu1 and tu2: a(freq=5), b(freq=4), c(freq=3), d/e/f(freq=1)
        title_to_ids = {
            "a": ["tu1", "tu2", "tu3", "tu4", "tu5"],
            "b": ["tu1", "tu2", "tu3", "tu4"],
            "c": ["tu1", "tu2", "tu3"],
            "d": ["tu1"],
            "e": ["tu1"],
            "f": ["tu1"],
        }
        nodes = _make_nodes_df(title_to_ids)
        edges = _extract_edges(
            title_to_ids,
            nodes,
            normalize_edge_weights=False,
            max_entities_per_chunk=3,
            min_co_occurrence=2,
        )
        # Top-3 in tu1: a, b, c → pairs: a-b, a-c, b-c
        # Top-3 in tu2: a, b, c → same pairs
        # Top-3 in tu3: a, b, c → same pairs
        # Top-3 in tu4: a, b (only 2 entities, no pairs from tu5)
        # a-b: tu1,tu2,tu3,tu4 (weight=4) ✓
        # a-c: tu1,tu2,tu3 (weight=3) ✓
        # b-c: tu1,tu2,tu3 (weight=3) ✓
        assert len(edges) == 3
        for _, row in edges.iterrows():
            assert row["weight"] >= 2

    def test_backward_compatible_defaults(self):
        """Default parameters produce the same result as original code."""
        title_to_ids = {
            "x": ["tu1", "tu2"],
            "y": ["tu1"],
            "z": ["tu2"],
        }
        nodes = _make_nodes_df(title_to_ids)

        edges_default = _extract_edges(
            title_to_ids, nodes, normalize_edge_weights=False
        )
        edges_explicit = _extract_edges(
            title_to_ids,
            nodes,
            normalize_edge_weights=False,
            max_entities_per_chunk=0,
            min_co_occurrence=1,
        )
        assert len(edges_default) == len(edges_explicit)
        assert set(
            zip(edges_default["source"], edges_default["target"])
        ) == set(
            zip(edges_explicit["source"], edges_explicit["target"])
        )
