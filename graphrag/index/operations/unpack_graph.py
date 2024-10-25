# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing unpack_graph, _run_unpack, _unpack_nodes and _unpack_edges methods definition."""

from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import VerbCallbacks, progress_iterable

from graphrag.index.utils.load_graph import load_graph

default_copy = ["level"]


def unpack_graph(
    input_df: pd.DataFrame,
    callbacks: VerbCallbacks,
    column: str,
    type: str,  # noqa A002
    copy: list[str] | None = None,
    embeddings_column: str = "embeddings",
) -> pd.DataFrame:
    """Unpack nodes or edges from a graphml graph, into a list of nodes or edges."""
    if copy is None:
        copy = default_copy

    num_total = len(input_df)
    result = []
    copy = [col for col in copy if col in input_df.columns]
    has_embeddings = embeddings_column in input_df.columns

    for _, row in progress_iterable(input_df.iterrows(), callbacks.progress, num_total):
        # merge the original row with the unpacked graph item
        cleaned_row = {col: row[col] for col in copy}
        embeddings = (
            cast(dict[str, list[float]], row[embeddings_column])
            if has_embeddings
            else {}
        )

        result.extend([
            {**cleaned_row, **graph_id}
            for graph_id in _run_unpack(
                cast(str | nx.Graph, row[column]),
                type,
                embeddings,
            )
        ])

    return pd.DataFrame(result)


def _run_unpack(
    graphml_or_graph: str | nx.Graph,
    unpack_type: str,
    embeddings: dict[str, list[float]],
) -> list[dict[str, Any]]:
    graph = load_graph(graphml_or_graph)
    if unpack_type == "nodes":
        return _unpack_nodes(graph, embeddings)
    if unpack_type == "edges":
        return _unpack_edges(graph)
    msg = f"Unknown type {unpack_type}"
    raise ValueError(msg)


def _unpack_nodes(
    graph: nx.Graph, embeddings: dict[str, list[float]]
) -> list[dict[str, Any]]:
    return [
        {
            "label": label,
            **(node_data or {}),
            "graph_embedding": embeddings.get(label),
        }
        for label, node_data in graph.nodes(data=True)  # type: ignore
    ]


def _unpack_edges(graph: nx.Graph) -> list[dict[str, Any]]:
    return [
        {
            "source": source_id,
            "target": target_id,
            **(edge_data or {}),
        }
        for source_id, target_id, edge_data in graph.edges(data=True)  # type: ignore
    ]
