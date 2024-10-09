# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing cluster_graph, apply_clustering and run_layout methods definition."""

import logging
from enum import Enum
from random import Random
from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import VerbCallbacks, progress_iterable
from graspologic.partition import hierarchical_leiden

from graphrag.index.graph.utils import stable_largest_connected_component
from graphrag.index.utils import gen_uuid, load_graph

Communities = list[tuple[int, str, list[str]]]


class GraphCommunityStrategyType(str, Enum):
    """GraphCommunityStrategyType class definition."""

    leiden = "leiden"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


log = logging.getLogger(__name__)


def cluster_graph(
    input: pd.DataFrame,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    column: str,
    to: str,
    level_to: str | None = None,
) -> pd.DataFrame:
    """Apply a hierarchical clustering algorithm to a graph."""
    results = input[column].apply(lambda graph: run_layout(strategy, graph))

    community_map_to = "communities"
    input[community_map_to] = results

    level_to = level_to or f"{to}_level"
    input[level_to] = input.apply(
        lambda x: list({level for level, _, _ in x[community_map_to]}), axis=1
    )
    input[to] = None

    num_total = len(input)

    # Create a seed for this run (if not provided)
    seed = strategy.get("seed", Random().randint(0, 0xFFFFFFFF))  # noqa S311

    # Go through each of the rows
    graph_level_pairs_column: list[list[tuple[int, str]]] = []
    for _, row in progress_iterable(input.iterrows(), callbacks.progress, num_total):
        levels = row[level_to]
        graph_level_pairs: list[tuple[int, str]] = []

        # For each of the levels, get the graph and add it to the list
        for level in levels:
            graph = "\n".join(
                nx.generate_graphml(
                    apply_clustering(
                        cast(str, row[column]),
                        cast(Communities, row[community_map_to]),
                        level,
                        seed=seed,
                    )
                )
            )
            graph_level_pairs.append((level, graph))
        graph_level_pairs_column.append(graph_level_pairs)
    input[to] = graph_level_pairs_column

    # explode the list of (level, graph) pairs into separate rows
    input = input.explode(to, ignore_index=True)

    # split the (level, graph) pairs into separate columns
    # TODO: There is probably a better way to do this
    input[[level_to, to]] = pd.DataFrame(input[to].tolist(), index=input.index)

    # clean up the community map
    input.drop(columns=[community_map_to], inplace=True)
    return input


# TODO: This should support str | nx.Graph as a graphml param
def apply_clustering(
    graphml: str, communities: Communities, level: int = 0, seed: int | None = None
) -> nx.Graph:
    """Apply clustering to a graphml string."""
    random = Random(seed)  # noqa S311
    graph = nx.parse_graphml(graphml)
    for community_level, community_id, nodes in communities:
        if level == community_level:
            for node in nodes:
                graph.nodes[node]["cluster"] = community_id
                graph.nodes[node]["level"] = level

    # add node degree
    for node_degree in graph.degree:
        graph.nodes[str(node_degree[0])]["degree"] = int(node_degree[1])

    # add node uuid and incremental record id (a human readable id used as reference in the final report)
    for index, node in enumerate(graph.nodes()):
        graph.nodes[node]["human_readable_id"] = index
        graph.nodes[node]["id"] = str(gen_uuid(random))

    # add ids to edges
    for index, edge in enumerate(graph.edges()):
        graph.edges[edge]["id"] = str(gen_uuid(random))
        graph.edges[edge]["human_readable_id"] = index
        graph.edges[edge]["level"] = level
    return graph


def run_layout(
    strategy: dict[str, Any], graphml_or_graph: str | nx.Graph
) -> Communities:
    """Run layout method definition."""
    graph = load_graph(graphml_or_graph)
    if len(graph.nodes) == 0:
        log.warning("Graph has no nodes")
        return []

    clusters: dict[int, dict[str, list[str]]] = {}
    strategy_type = strategy.get("type", GraphCommunityStrategyType.leiden)
    match strategy_type:
        case GraphCommunityStrategyType.leiden:
            clusters = run_leiden(graph, strategy)
        case _:
            msg = f"Unknown clustering strategy {strategy_type}"
            raise ValueError(msg)

    results: Communities = []
    for level in clusters:
        for cluster_id, nodes in clusters[level].items():
            results.append((level, cluster_id, nodes))
    return results


def run_leiden(
    graph: nx.Graph, args: dict[str, Any]
) -> dict[int, dict[str, list[str]]]:
    """Run method definition."""
    max_cluster_size = args.get("max_cluster_size", 10)
    use_lcc = args.get("use_lcc", True)
    if args.get("verbose", False):
        log.info(
            "Running leiden with max_cluster_size=%s, lcc=%s", max_cluster_size, use_lcc
        )

    node_id_to_community_map = _compute_leiden_communities(
        graph=graph,
        max_cluster_size=max_cluster_size,
        use_lcc=use_lcc,
        seed=args.get("seed", 0xDEADBEEF),
    )
    levels = args.get("levels")

    # If they don't pass in levels, use them all
    if levels is None:
        levels = sorted(node_id_to_community_map.keys())

    results_by_level: dict[int, dict[str, list[str]]] = {}
    for level in levels:
        result = {}
        results_by_level[level] = result
        for node_id, raw_community_id in node_id_to_community_map[level].items():
            community_id = str(raw_community_id)
            if community_id not in result:
                result[community_id] = []
            result[community_id].append(node_id)
    return results_by_level


# Taken from graph_intelligence & adapted
def _compute_leiden_communities(
    graph: nx.Graph | nx.DiGraph,
    max_cluster_size: int,
    use_lcc: bool,
    seed=0xDEADBEEF,
) -> dict[int, dict[str, int]]:
    """Return Leiden root communities."""
    if use_lcc:
        graph = stable_largest_connected_component(graph)

    community_mapping = hierarchical_leiden(
        graph, max_cluster_size=max_cluster_size, random_seed=seed
    )
    results: dict[int, dict[str, int]] = {}
    for partition in community_mapping:
        results[partition.level] = results.get(partition.level, {})
        results[partition.level][partition.node] = partition.cluster

    return results
