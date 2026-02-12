# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Side-by-side tests comparing NetworkX connected components with DataFrame-based implementation."""

import json
from pathlib import Path

import networkx as nx
import pandas as pd
from graphrag.graphs.connected_components import (
    connected_components,
    largest_connected_component,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture() -> pd.DataFrame:
    """Load the realistic graph fixture as a relationships DataFrame."""
    with open(FIXTURES_DIR / "graph.json") as f:
        data = json.load(f)
    return pd.DataFrame(data["edges"])


def _make_relationships(*edges: tuple[str, str, float]) -> pd.DataFrame:
    """Build a relationships DataFrame from (source, target, weight) tuples."""
    return pd.DataFrame([{"source": s, "target": t, "weight": w} for s, t, w in edges])


# ---------------------------------------------------------------------------
# NetworkX reference helpers
# ---------------------------------------------------------------------------


def _nx_connected_components(relationships: pd.DataFrame) -> list[set[str]]:
    """Compute connected components using NetworkX."""
    graph = nx.from_pandas_edgelist(relationships, source="source", target="target")
    return sorted(
        [set(c) for c in nx.connected_components(graph)],
        key=len,
        reverse=True,
    )


def _nx_largest_connected_component(relationships: pd.DataFrame) -> set[str]:
    """Return the LCC using NetworkX."""
    components = _nx_connected_components(relationships)
    return components[0] if components else set()


# ---------------------------------------------------------------------------
# Simple topology tests
# ---------------------------------------------------------------------------


def test_single_component():
    """Fully connected graph should have one component."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("A", "C", 1.0),
    )
    nx_components = _nx_connected_components(rels)
    df_components = connected_components(rels)
    assert len(nx_components) == len(df_components) == 1
    assert nx_components[0] == df_components[0]


def test_two_components():
    """Two disconnected pairs should give two components."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("C", "D", 1.0),
    )
    nx_components = _nx_connected_components(rels)
    df_components = connected_components(rels)
    assert len(nx_components) == len(df_components) == 2
    assert {frozenset(c) for c in nx_components} == {
        frozenset(c) for c in df_components
    }


def test_three_components_lcc():
    """LCC should pick the largest of three components."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("A", "C", 1.0),
        ("A", "D", 1.0),
        ("X", "Y", 1.0),
        ("P", "Q", 1.0),
    )
    nx_lcc = _nx_largest_connected_component(rels)
    df_lcc = largest_connected_component(rels)
    assert nx_lcc == df_lcc
    assert df_lcc == {"A", "B", "C", "D"}


def test_star_topology():
    """Star should be a single component."""
    rels = _make_relationships(
        ("hub", "a", 1.0),
        ("hub", "b", 1.0),
        ("hub", "c", 1.0),
    )
    df_lcc = largest_connected_component(rels)
    nx_lcc = _nx_largest_connected_component(rels)
    assert df_lcc == nx_lcc == {"hub", "a", "b", "c"}


def test_duplicate_edges():
    """Duplicate edges should not affect component membership."""
    rels = _make_relationships(
        ("A", "B", 1.0),
        ("A", "B", 2.0),
        ("C", "D", 1.0),
    )
    nx_components = _nx_connected_components(rels)
    df_components = connected_components(rels)
    assert len(nx_components) == len(df_components) == 2
    assert {frozenset(c) for c in nx_components} == {
        frozenset(c) for c in df_components
    }


def test_empty_relationships():
    """Empty edge list should produce no components."""
    rels = pd.DataFrame(columns=["source", "target", "weight"])
    assert connected_components(rels) == []
    assert largest_connected_component(rels) == set()


# ---------------------------------------------------------------------------
# Realistic fixture tests
# ---------------------------------------------------------------------------


def test_fixture_component_count():
    """Component count should match NetworkX on the realistic fixture."""
    rels = _load_fixture()
    nx_components = _nx_connected_components(rels)
    df_components = connected_components(rels)
    assert len(df_components) == len(nx_components)


def test_fixture_component_sizes():
    """Component sizes (sorted desc) should match NetworkX."""
    rels = _load_fixture()
    nx_sizes = [len(c) for c in _nx_connected_components(rels)]
    df_sizes = [len(c) for c in connected_components(rels)]
    assert df_sizes == nx_sizes


def test_fixture_lcc_membership():
    """LCC membership should be identical to NetworkX."""
    rels = _load_fixture()
    nx_lcc = _nx_largest_connected_component(rels)
    df_lcc = largest_connected_component(rels)
    assert df_lcc == nx_lcc


def test_fixture_lcc_size():
    """LCC should contain 535 nodes (known from the fixture)."""
    rels = _load_fixture()
    lcc = largest_connected_component(rels)
    assert len(lcc) == 535
