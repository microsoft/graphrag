# Copyright (C) 2026 Microsoft

"""Tests for the cluster_graph operation.

These tests pin down the behavior of cluster_graph and its internal
_compute_leiden_communities function so that refactoring (vectorizing
iterrows, reducing copies, etc.) can be verified against known output.
"""

import pandas as pd
import pytest
from graphrag.index.operations.cluster_graph import (
    Communities,
    cluster_graph,
)


def _make_edges(
    rows: list[tuple[str, str, float]],
) -> pd.DataFrame:
    """Build a minimal relationships DataFrame from (source, target, weight)."""
    return pd.DataFrame([{"source": s, "target": t, "weight": w} for s, t, w in rows])


def _node_sets(clusters: Communities) -> list[set[str]]:
    """Extract sorted-by-level list of node sets from cluster output."""
    return [set(nodes) for _, _, _, nodes in clusters]


# -------------------------------------------------------------------
# Basic clustering
# -------------------------------------------------------------------


class TestClusterGraphBasic:
    """Verify basic clustering on small synthetic graphs."""

    def test_single_triangle(self):
        """A single triangle should produce one community at level 0."""
        edges = _make_edges([("X", "Y", 1.0), ("X", "Z", 1.0), ("Y", "Z", 1.0)])
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        assert len(clusters) == 1
        level, _cid, parent, nodes = clusters[0]
        assert level == 0
        assert parent == -1
        assert set(nodes) == {"X", "Y", "Z"}

    def test_two_disconnected_cliques(self):
        """Two disconnected triangles should produce two communities."""
        edges = _make_edges([
            ("A", "B", 1.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
            ("D", "E", 1.0),
            ("D", "F", 1.0),
            ("E", "F", 1.0),
        ])
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        assert len(clusters) == 2
        node_sets = _node_sets(clusters)
        assert {"A", "B", "C"} in node_sets
        assert {"D", "E", "F"} in node_sets
        for level, _, parent, _ in clusters:
            assert level == 0
            assert parent == -1

    def test_lcc_filters_to_largest_component(self):
        """With use_lcc=True, only the largest connected component is kept."""
        edges = _make_edges([
            ("A", "B", 1.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
            ("D", "E", 1.0),
            ("D", "F", 1.0),
            ("E", "F", 1.0),
        ])
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=True, seed=42)

        assert len(clusters) == 1
        all_nodes = set(clusters[0][3])
        assert len(all_nodes) == 3


# -------------------------------------------------------------------
# Edge normalization
# -------------------------------------------------------------------


class TestEdgeNormalization:
    """Verify that direction normalization and deduplication work."""

    def test_reversed_edges_produce_same_result(self):
        """Reversing all edge directions should yield identical clusters."""
        forward = _make_edges([
            ("A", "B", 1.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
            ("D", "E", 1.0),
            ("D", "F", 1.0),
            ("E", "F", 1.0),
        ])
        backward = _make_edges([
            ("B", "A", 1.0),
            ("C", "A", 1.0),
            ("C", "B", 1.0),
            ("E", "D", 1.0),
            ("F", "D", 1.0),
            ("F", "E", 1.0),
        ])
        clusters_fwd = cluster_graph(
            forward, max_cluster_size=10, use_lcc=False, seed=42
        )
        clusters_bwd = cluster_graph(
            backward, max_cluster_size=10, use_lcc=False, seed=42
        )

        assert _node_sets(clusters_fwd) == _node_sets(clusters_bwd)

    def test_duplicate_edges_are_deduped(self):
        """A→B and B→A should be treated as one edge after normalization."""
        edges = _make_edges([
            ("A", "B", 1.0),
            ("B", "A", 2.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
        ])
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        assert len(clusters) == 1
        assert set(clusters[0][3]) == {"A", "B", "C"}

    def test_missing_weight_defaults_to_one(self):
        """Edges without a weight column should default to weight 1.0."""
        edges = pd.DataFrame({
            "source": ["A", "A", "B"],
            "target": ["B", "C", "C"],
        })
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        assert len(clusters) == 1
        assert set(clusters[0][3]) == {"A", "B", "C"}


# -------------------------------------------------------------------
# Determinism
# -------------------------------------------------------------------


class TestDeterminism:
    """Verify that seeding produces reproducible results."""

    def test_same_seed_same_result(self):
        """Identical seed should yield identical output."""
        edges = _make_edges([
            ("A", "B", 1.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
            ("D", "E", 1.0),
            ("D", "F", 1.0),
            ("E", "F", 1.0),
        ])
        c1 = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=123)
        c2 = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=123)

        assert c1 == c2

    def test_does_not_mutate_input(self):
        """cluster_graph should not modify the input DataFrame."""
        edges = _make_edges([
            ("A", "B", 1.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
        ])
        original = edges.copy()
        cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        pd.testing.assert_frame_equal(edges, original)


# -------------------------------------------------------------------
# Output structure
# -------------------------------------------------------------------


class TestOutputStructure:
    """Verify the shape and types of the Communities output."""

    def test_output_tuple_structure(self):
        """Each entry should be (level, community_id, parent, node_list)."""
        edges = _make_edges([("A", "B", 1.0), ("A", "C", 1.0), ("B", "C", 1.0)])
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        for entry in clusters:
            assert len(entry) == 4
            level, cid, parent, nodes = entry
            assert isinstance(level, int)
            assert isinstance(cid, int)
            assert isinstance(parent, int)
            assert isinstance(nodes, list)
            assert all(isinstance(n, str) for n in nodes)

    def test_level_zero_has_parent_minus_one(self):
        """All level-0 clusters should have parent == -1."""
        edges = _make_edges([
            ("A", "B", 1.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
            ("D", "E", 1.0),
            ("D", "F", 1.0),
            ("E", "F", 1.0),
        ])
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        for level, _, parent, _ in clusters:
            if level == 0:
                assert parent == -1

    def test_all_nodes_covered_at_each_level(self):
        """At any given level, the union of all community nodes should
        equal exactly the set of all nodes in the graph for that level."""
        edges = _make_edges([
            ("A", "B", 1.0),
            ("A", "C", 1.0),
            ("B", "C", 1.0),
            ("D", "E", 1.0),
            ("D", "F", 1.0),
            ("E", "F", 1.0),
        ])
        clusters = cluster_graph(edges, max_cluster_size=10, use_lcc=False, seed=42)

        levels: dict[int, set[str]] = {}
        for level, _, _, nodes in clusters:
            levels.setdefault(level, set()).update(nodes)

        all_nodes = {"A", "B", "C", "D", "E", "F"}
        for level, covered_nodes in levels.items():
            assert covered_nodes == all_nodes, (
                f"Level {level}: expected {all_nodes}, got {covered_nodes}"
            )


# -------------------------------------------------------------------
# Real test data (golden file regression)
# -------------------------------------------------------------------


class TestClusterGraphRealData:
    """Regression tests using the shared test fixture data."""

    @pytest.fixture
    def relationships(self) -> pd.DataFrame:
        """Load the test relationships fixture."""
        return pd.read_parquet("tests/verbs/data/relationships.parquet")

    def test_cluster_count(self, relationships: pd.DataFrame):
        """Pin the expected number of clusters from the fixture data."""
        clusters = cluster_graph(
            relationships,
            max_cluster_size=10,
            use_lcc=True,
            seed=0xDEADBEEF,
        )
        assert len(clusters) == 122

    def test_level_distribution(self, relationships: pd.DataFrame):
        """Pin the expected number of clusters per level."""
        clusters = cluster_graph(
            relationships,
            max_cluster_size=10,
            use_lcc=True,
            seed=0xDEADBEEF,
        )
        from collections import Counter

        level_counts = Counter(c[0] for c in clusters)
        assert level_counts == {0: 23, 1: 65, 2: 32, 3: 2}

    def test_level_zero_nodes_sample(self, relationships: pd.DataFrame):
        """Spot-check a few known nodes in level-0 clusters."""
        clusters = cluster_graph(
            relationships,
            max_cluster_size=10,
            use_lcc=True,
            seed=0xDEADBEEF,
        )
        level_0 = [c for c in clusters if c[0] == 0]
        all_level_0_nodes = set()
        for _, _, _, nodes in level_0:
            all_level_0_nodes.update(nodes)

        assert "SCROOGE" in all_level_0_nodes
        assert "ABRAHAM" in all_level_0_nodes
        assert "JACOB MARLEY" in all_level_0_nodes
