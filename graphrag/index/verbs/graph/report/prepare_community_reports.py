# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_community_reports and load_strategy methods definition."""

from enum import Enum
from random import Random
from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import (
    AsyncType,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    derive_from_rows,
    verb,
)

from graphrag.index.graph.extractors import prep_community_reports_data
from graphrag.index.graph.utils import stable_largest_connected_component
from graphrag.index.utils import gen_uuid, load_graph

DEFAULT_INPUT_LENGTH = 12_000


class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"


@verb(name="prepare_community_reports")
async def prepare_community_reports(
    input: VerbInput,
    callbacks: VerbCallbacks,
    graph_column: str,
    strategy: dict[str, Any],
    level_column: str = "level",
    claims_column: str | None = None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    **kwargs,
) -> TableContainer:
    """Generate entities for each row, and optionally a graph of those entities."""
    strategy_args = {**strategy}

    async def prepare_row(row) -> tuple[list[str], list[int], list[dict]]:
        claims = row[claims_column] if claims_column is not None else None
        graph_xml: str = cast(str, row[graph_column])
        level = row[level_column]
        graph = load_graph(graph_xml)

        nodes, edges = _load_nodes_edges_for_claim_chain(
            graph, strategy_args.get("use_lcc", True)
        )
        max_input_length = strategy_args.get("max_input_length", DEFAULT_INPUT_LENGTH)
        input_data = prep_community_reports_data(
            nodes=nodes,
            edges=edges,
            claims=cast(list[dict] | None, claims),
            max_tokens=max_input_length,
        )

        excluded_communities = strategy_args.get("excluded_communities", [])
        communities = sorted([c for c in input_data if c not in excluded_communities])
        levels = [level] * len(communities)
        input = [input_data[community] for community in communities]
        return communities, levels, input

    results = await derive_from_rows(
        cast(pd.DataFrame, input.get_input()),
        prepare_row,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )

    all_communities: list[str] = []
    all_levels: list[int] = []
    all_input: list[dict] = []
    for t in results:
        if t is not None:
            t_communities, t_levels, t_in = t
            all_communities += t_communities
            all_levels += t_levels
            all_input += t_in

    return TableContainer(
        table=pd.DataFrame({
            "community": all_communities,
            "input": all_input,
            "level": all_levels,
        })
    )


def _load_nodes_edges_for_claim_chain(
    graph: nx.Graph,
    use_lcc: bool,
    seed: int = 0xD3ADF00D,
) -> tuple[list[dict], list[dict]]:
    nodes = []
    random = Random(seed)  # noqa S311

    if use_lcc:
        graph = stable_largest_connected_component(graph)

    # The extra "sorted" here, ensures that if we run the same graph twice, we get the same results
    for index, node in enumerate(sorted(graph.nodes(data=True), key=lambda x: x[0])):
        if node is not None:
            node_attributes = node[1] or {}
            node_attributes["label"] = node[0]
            node_attributes["record_id"] = index
            nodes.append(node_attributes)

    edges = []

    # The extra "sorted" here, ensures that if we run the same graph twice, we get the same results
    for index, edge in enumerate(sorted(graph.edges(data=True), key=lambda x: x[0])):
        if edge is not None:
            edge_attributes = edge[2] or {}  # type: ignore
            edge_attributes["source"] = edge[0]
            edge_attributes["target"] = edge[1]
            edge_attributes["record_id"] = index
            edge_attributes["id"] = gen_uuid(random)
            edges.append(edge_attributes)
    return nodes, edges
