# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Side-by-side tests for the DataFrame-based modularity utility."""

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
from graphrag.graphs.modularity import modularity

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# NX reference implementation (copied from graphrag.index.utils.graphs)
# ---------------------------------------------------------------------------


def _nx_modularity_component(
    intra_community_degree: float,
    total_community_degree: float,
    network_degree_sum: float,
    resolution: float,
) -> float:
    community_degree_ratio = math.pow(total_community_degree, 2.0) / (
        2.0 * network_degree_sum
    )
    return (intra_community_degree - resolution * community_degree_ratio) / (
        2.0 * network_degree_sum
    )


def _nx_modularity_components(
    graph: nx.Graph,
    partitions: dict[Any, int],
    weight_attribute: str = "weight",
    resolution: float = 1.0,
) -> dict[int, float]:
    total_edge_weight = 0.0
    communities = set(partitions.values())

    degree_sums_within_community: dict[int, float] = defaultdict(float)
    degree_sums_for_community: dict[int, float] = defaultdict(float)
    for vertex, neighbor_vertex, weight in graph.edges(data=weight_attribute):
        vertex_community = partitions[vertex]
        neighbor_community = partitions[neighbor_vertex]
        if vertex_community == neighbor_community:
            if vertex == neighbor_vertex:
                degree_sums_within_community[vertex_community] += weight
            else:
                degree_sums_within_community[vertex_community] += weight * 2.0
        degree_sums_for_community[vertex_community] += weight
        degree_sums_for_community[neighbor_community] += weight
        total_edge_weight += weight

    return {
        comm: _nx_modularity_component(
            degree_sums_within_community[comm],
            degree_sums_for_community[comm],
            total_edge_weight,
            resolution,
        )
        for comm in communities
    }


def nx_modularity(
    graph: nx.Graph,
    partitions: dict[Any, int],
    weight_attribute: str = "weight",
    resolution: float = 1.0,
) -> float:
    """NX reference: compute modularity from a networkx graph."""
    components = _nx_modularity_components(
        graph, partitions, weight_attribute, resolution
    )
    return sum(components.values())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_fixture() -> pd.DataFrame:
    """Load the realistic graph fixture as a relationships DataFrame."""
    with open(FIXTURES_DIR / "graph.json") as f:
        data = json.load(f)
    return pd.DataFrame(data["edges"])


def _make_edges(*edges: tuple[str, str, float]) -> pd.DataFrame:
    """Build a relationships DataFrame from (source, target, weight) tuples."""
    return pd.DataFrame([{"source": s, "target": t, "weight": w} for s, t, w in edges])


def _edges_to_nx(edges: pd.DataFrame) -> nx.Graph:
    """Build an NX graph from an edges DataFrame."""
    return nx.from_pandas_edgelist(edges, edge_attr=["weight"])


# ---------------------------------------------------------------------------
# Side-by-side tests
# ---------------------------------------------------------------------------


def test_two_clear_communities():
    """Two densely-connected communities with a weak bridge."""
    edges = _make_edges(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("A", "C", 1.0),
        ("D", "E", 1.0),
        ("E", "F", 1.0),
        ("D", "F", 1.0),
        ("C", "D", 0.1),
    )
    partitions = {"A": 0, "B": 0, "C": 0, "D": 1, "E": 1, "F": 1}

    nx_result = nx_modularity(_edges_to_nx(edges), partitions)
    df_result = modularity(edges, partitions)

    assert abs(nx_result - df_result) < 1e-10
    assert df_result > 0  # good partition should be positive


def test_single_community():
    """All nodes in one community — modularity should be zero."""
    edges = _make_edges(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("A", "C", 1.0),
    )
    partitions = {"A": 0, "B": 0, "C": 0}

    nx_result = nx_modularity(_edges_to_nx(edges), partitions)
    df_result = modularity(edges, partitions)

    assert abs(nx_result - df_result) < 1e-10
    assert abs(df_result) < 1e-10


def test_every_node_own_community():
    """Each node in its own community — modularity should be negative."""
    edges = _make_edges(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("A", "C", 1.0),
    )
    partitions = {"A": 0, "B": 1, "C": 2}

    nx_result = nx_modularity(_edges_to_nx(edges), partitions)
    df_result = modularity(edges, partitions)

    assert abs(nx_result - df_result) < 1e-10
    assert df_result < 0


def test_reversed_edges():
    """Reversed edge direction should not affect modularity (undirected)."""
    edges_fwd = _make_edges(("A", "B", 1.0), ("B", "C", 1.0), ("C", "D", 1.0))
    edges_rev = _make_edges(("B", "A", 1.0), ("C", "B", 1.0), ("D", "C", 1.0))
    partitions = {"A": 0, "B": 0, "C": 1, "D": 1}

    fwd = modularity(edges_fwd, partitions)
    rev = modularity(edges_rev, partitions)

    assert abs(fwd - rev) < 1e-10


def test_weighted_edges():
    """Different weights should affect modularity."""
    edges_uniform = _make_edges(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("C", "D", 1.0),
    )
    edges_weighted = _make_edges(
        ("A", "B", 5.0),
        ("B", "C", 0.1),
        ("C", "D", 5.0),
    )
    partitions = {"A": 0, "B": 0, "C": 1, "D": 1}

    u_nx = nx_modularity(_edges_to_nx(edges_uniform), partitions)
    u_df = modularity(edges_uniform, partitions)
    w_nx = nx_modularity(_edges_to_nx(edges_weighted), partitions)
    w_df = modularity(edges_weighted, partitions)

    assert abs(u_nx - u_df) < 1e-10
    assert abs(w_nx - w_df) < 1e-10
    # weighted version should have higher modularity (strong intra, weak inter)
    assert w_df > u_df


def test_custom_resolution():
    """Resolution parameter should affect result and match NX."""
    edges = _make_edges(
        ("A", "B", 1.0),
        ("B", "C", 1.0),
        ("A", "C", 1.0),
        ("D", "E", 1.0),
        ("C", "D", 0.5),
    )
    partitions = {"A": 0, "B": 0, "C": 0, "D": 1, "E": 1}
    graph = _edges_to_nx(edges)

    for res in (0.5, 1.0, 2.0):
        nx_r = nx_modularity(graph, partitions, resolution=res)
        df_r = modularity(edges, partitions, resolution=res)
        assert abs(nx_r - df_r) < 1e-10


def test_duplicate_edges():
    """Duplicate edges (same pair, different weights) should match NX dedup."""
    edges = _make_edges(
        ("A", "B", 1.0),
        ("A", "B", 3.0),  # duplicate — NX keeps last
        ("B", "C", 2.0),
    )
    partitions = {"A": 0, "B": 0, "C": 1}

    nx_result = nx_modularity(_edges_to_nx(edges), partitions)
    df_result = modularity(edges, partitions)

    assert abs(nx_result - df_result) < 1e-10


def test_reversed_duplicate_edges():
    """Edge (A,B) and (B,A) should be treated as the same, keeping last weight."""
    edges = _make_edges(
        ("A", "B", 1.0),
        ("B", "A", 5.0),  # reversed duplicate — NX keeps 5.0
        ("B", "C", 2.0),
    )
    partitions = {"A": 0, "B": 0, "C": 1}

    nx_result = nx_modularity(_edges_to_nx(edges), partitions)
    df_result = modularity(edges, partitions)

    assert abs(nx_result - df_result) < 1e-10


def test_fixture_matches_nx():
    """Modularity on the fixture graph should match NX for several partitions."""
    edges = _load_fixture()
    graph = _edges_to_nx(edges)
    nodes = sorted(graph.nodes())

    # Test with a few different partition schemes
    for n_communities in (2, 3, 5):
        partitions = {node: i % n_communities for i, node in enumerate(nodes)}
        nx_result = nx_modularity(graph, partitions)
        df_result = modularity(edges, partitions)
        assert abs(nx_result - df_result) < 1e-10, (
            f"Mismatch for {n_communities} communities: NX={nx_result}, DF={df_result}"
        )
