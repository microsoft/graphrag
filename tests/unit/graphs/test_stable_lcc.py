# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Side-by-side tests for the DataFrame-based stable LCC utility."""

import json
from pathlib import Path

import networkx as nx
import pandas as pd
from graphrag.graphs.stable_lcc import stable_lcc
from pandas.testing import assert_frame_equal

from tests.unit.graphs.nx_stable_lcc import stable_largest_connected_component

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture() -> pd.DataFrame:
    """Load the realistic graph fixture as a relationships DataFrame."""
    with open(FIXTURES_DIR / "graph.json") as f:
        data = json.load(f)
    return pd.DataFrame(data["edges"])


def _make_relationships(*edges: tuple[str, str, float]) -> pd.DataFrame:
    """Build a relationships DataFrame from (source, target, weight) tuples."""
    return pd.DataFrame([{"source": s, "target": t, "weight": w} for s, t, w in edges])


def _nx_stable_lcc_node_set(relationships: pd.DataFrame) -> set[str]:
    """Get the node set from the NX stable_largest_connected_component."""
    graph = nx.from_pandas_edgelist(
        relationships,
        source="source",
        target="target",
        edge_attr=["weight"],
    )
    stable_graph = stable_largest_connected_component(graph)
    return set(stable_graph.nodes())


def _nx_stable_lcc_edge_set(relationships: pd.DataFrame) -> set[tuple[str, str]]:
    """Get the edge set from the NX stable_largest_connected_component."""
    graph = nx.from_pandas_edgelist(
        relationships,
        source="source",
        target="target",
        edge_attr=["weight"],
    )
    stable_graph = stable_largest_connected_component(graph)
    return {(min(s, t), max(s, t)) for s, t in stable_graph.edges()}


# ---------------------------------------------------------------------------
# Stability tests
# ---------------------------------------------------------------------------


def test_flipped_edges_produce_same_result():
    """Same graph with edges in different direction should produce identical output."""
    rels_1 = _make_relationships(
        ("A", "B", 1.0),
        ("B", "C", 2.0),
        ("C", "D", 3.0),
        ("D", "E", 4.0),
    )
    rels_2 = _make_relationships(
        ("B", "A", 1.0),
        ("C", "B", 2.0),
        ("D", "C", 3.0),
        ("E", "D", 4.0),
    )
    result_1 = stable_lcc(rels_1)
    result_2 = stable_lcc(rels_2)
    assert_frame_equal(result_1, result_2)


def test_shuffled_rows_produce_same_result():
    """Different row order should produce identical output."""
    rels_1 = _make_relationships(
        ("A", "B", 1.0),
        ("B", "C", 2.0),
        ("C", "D", 3.0),
    )
    rels_2 = _make_relationships(
        ("C", "D", 3.0),
        ("A", "B", 1.0),
        ("B", "C", 2.0),
    )
    result_1 = stable_lcc(rels_1)
    result_2 = stable_lcc(rels_2)
    assert_frame_equal(result_1, result_2)


# ---------------------------------------------------------------------------
# Name normalization tests
# ---------------------------------------------------------------------------


def test_normalizes_node_names():
    """Node names should be uppercased, stripped, and HTML-unescaped."""
    rels = _make_relationships(
        ("  alice  ", "bob", 1.0),
        ("bob", "carol &amp; dave", 1.0),
    )
    result = stable_lcc(rels)
    all_nodes = set(result["source"]).union(result["target"])
    assert "ALICE" in all_nodes
    assert "BOB" in all_nodes
    assert "CAROL & DAVE" in all_nodes


# ---------------------------------------------------------------------------
# LCC filtering tests
# ---------------------------------------------------------------------------


def test_filters_to_lcc():
    """Only the largest component should remain."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("C", "A", 1.0),
        ("X", "Y", 1.0),
    )
    result = stable_lcc(rels)
    all_nodes = set(result["source"]).union(result["target"])
    assert all_nodes == {"A", "B", "C"}


def test_empty_relationships():
    """Empty input should return empty output."""
    rels = pd.DataFrame(columns=["source", "target", "weight"])
    result = stable_lcc(rels)
    assert result.empty


# ---------------------------------------------------------------------------
# Side-by-side with NX implementation
# ---------------------------------------------------------------------------


def test_node_set_matches_nx():
    """LCC node set should match the NX stable_largest_connected_component."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("C", "D", 1.0),
        ("D", "E", 1.0),
        ("X", "Y", 1.0),
    )
    nx_nodes = _nx_stable_lcc_node_set(rels)
    df_result = stable_lcc(rels)
    df_nodes = set(df_result["source"]).union(df_result["target"])
    assert df_nodes == nx_nodes


def test_edge_set_matches_nx():
    """LCC edge set should match the NX stable_largest_connected_component."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("C", "D", 1.0),
        ("D", "E", 1.0),
        ("X", "Y", 1.0),
    )
    nx_edges = _nx_stable_lcc_edge_set(rels)
    df_result = stable_lcc(rels)
    df_edges = {
        (min(s, t), max(s, t))
        for s, t in zip(df_result["source"], df_result["target"], strict=True)
    }
    assert df_edges == nx_edges


# ---------------------------------------------------------------------------
# Fixture tests
# ---------------------------------------------------------------------------


def test_fixture_node_set_matches_nx():
    """Fixture LCC nodes should match NX stable LCC."""
    rels = _load_fixture()
    nx_nodes = _nx_stable_lcc_node_set(rels)
    df_result = stable_lcc(rels)
    df_nodes = set(df_result["source"]).union(df_result["target"])
    assert df_nodes == nx_nodes


def test_fixture_edge_set_matches_nx():
    """Fixture LCC edges should match NX stable LCC."""
    rels = _load_fixture()
    nx_edges = _nx_stable_lcc_edge_set(rels)
    df_result = stable_lcc(rels)
    df_edges = {
        (min(s, t), max(s, t))
        for s, t in zip(df_result["source"], df_result["target"], strict=True)
    }
    assert df_edges == nx_edges


def test_fixture_edges_are_sorted():
    """Output edges should be sorted with source <= target and rows in order."""
    rels = _load_fixture()
    result = stable_lcc(rels)
    # Every source should be <= target
    assert (result["source"] <= result["target"]).all()
    # Rows should be sorted
    is_sorted = (
        result[["source", "target"]].apply(tuple, axis=1).is_monotonic_increasing
    )
    assert is_sorted
