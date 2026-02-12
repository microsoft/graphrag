# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Side-by-side tests comparing NetworkX compute_degree with DataFrame-based compute_degree_df."""

import json
from pathlib import Path

import networkx as nx
import pandas as pd
from graphrag.graphs.compute_degree import compute_degree as compute_degree_df
from pandas.testing import assert_frame_equal

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_relationships(*edges: tuple[str, str, float]) -> pd.DataFrame:
    """Build a relationships DataFrame from (source, target, weight) tuples."""
    return pd.DataFrame([{"source": s, "target": t, "weight": w} for s, t, w in edges])


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by title and reset index for comparison."""
    return df.sort_values("title").reset_index(drop=True)


def _compute_degree_via_nx(relationships: pd.DataFrame) -> pd.DataFrame:
    """Compute degree using NetworkX directly."""
    graph = nx.from_pandas_edgelist(
        relationships, source="source", target="target", edge_attr=["weight"]
    )
    return pd.DataFrame([
        {"title": node, "degree": int(degree)} for node, degree in graph.degree
    ])


def test_simple_triangle():
    """Three nodes forming a triangle — each should have degree 2."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("A", "C", 1.0),
    )
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)


def test_star_topology():
    """One hub connected to many leaves."""
    rels = _make_relationships(
        ("hub", "a", 1.0),
        ("hub", "b", 1.0),
        ("hub", "c", 1.0),
        ("hub", "d", 1.0),
    )
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)
    # hub should have degree 4
    hub_row = df_result[df_result["title"] == "hub"]
    assert hub_row["degree"].iloc[0] == 4


def test_disconnected_components():
    """Two separate components."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("C", "D", 1.0),
    )
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)


def test_single_edge():
    """Simplest case: one edge, two nodes, each with degree 1."""
    rels = _make_relationships(("X", "Y", 1.0))
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)


def test_self_loop():
    """A self-loop contributes degree 2 in NetworkX for undirected graphs."""
    rels = _make_relationships(
        ("A", "A", 1.0),
        ("A", "B", 1.0),
    )
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)


def test_duplicate_edges():
    """Duplicate edges in the DataFrame — NetworkX deduplicates, so should we check behavior."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("A", "B", 2.0),
        ("B", "C", 1.0),
    )
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)


def test_larger_graph():
    """A larger graph to exercise multiple degree values."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("A", "C", 1.0),
        ("A", "D", 1.0),
        ("B", "C", 1.0),
        ("D", "E", 1.0),
        ("E", "F", 1.0),
    )
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)


def test_fixture_graph():
    """Degree computation on the realistic A Christmas Carol fixture should match NetworkX."""
    with open(FIXTURES_DIR / "graph.json") as f:
        data = json.load(f)
    rels = pd.DataFrame(data["edges"])
    nx_result = _normalize(_compute_degree_via_nx(rels))
    df_result = _normalize(compute_degree_df(rels))
    assert_frame_equal(nx_result, df_result)
    assert len(df_result) > 500  # sanity: realistic graph has 500+ nodes
