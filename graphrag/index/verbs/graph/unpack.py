# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing unpack_graph, _run_unpack, _unpack_nodes and _unpack_edges methods definition."""

from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, progress_iterable, verb

from graphrag.index.utils import load_graph

default_copy = ["level"]


@verb(name="unpack_graph")
def unpack_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    column: str,
    type: str,  # noqa A002
    copy: list[str] | None = None,
    embeddings_column: str = "embeddings",
    **kwargs,
) -> TableContainer:
    """
    Unpack nodes or edges from a graphml graph, into a list of nodes or edges.

    This verb will create columns for each attribute in a node or edge.

    ## Usage
    ```yaml
    verb: unpack_graph
    args:
        type: node # The type of data to unpack, one of: node, edge. node will create a node list, edge will create an edge list
        column: <column name> # The name of the column containing the graph, should be a graphml graph
    ```
    """
    input_df = input.get_input()
    output_df = unpack_graph_df(
        cast(pd.DataFrame, input_df),
        callbacks,
        column,
        type,
        copy,
        embeddings_column,
        kwargs=kwargs,
    )
    return TableContainer(table=output_df)


def unpack_graph_df(
    input_df: pd.DataFrame,
    callbacks: VerbCallbacks,
    column: str,
    type: str,  # noqa A002
    copy: list[str] | None = None,
    embeddings_column: str = "embeddings",
    **kwargs,
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
                kwargs,
            )
        ])

    return pd.DataFrame(result)


def _run_unpack(
    graphml_or_graph: str | nx.Graph,
    unpack_type: str,
    embeddings: dict[str, list[float]],
    args: dict[str, Any],
) -> list[dict[str, Any]]:
    graph = load_graph(graphml_or_graph)
    if unpack_type == "nodes":
        return _unpack_nodes(graph, embeddings, args)
    if unpack_type == "edges":
        return _unpack_edges(graph, args)
    msg = f"Unknown type {unpack_type}"
    raise ValueError(msg)


def _unpack_nodes(
    graph: nx.Graph, embeddings: dict[str, list[float]], _args: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "label": label,
            **(node_data or {}),
            "graph_embedding": embeddings.get(label),
        }
        for label, node_data in graph.nodes(data=True)  # type: ignore
    ]


def _unpack_edges(graph: nx.Graph, _args: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source": source_id,
            "target": target_id,
            **(edge_data or {}),
        }
        for source_id, target_id, edge_data in graph.edges(data=True)  # type: ignore
    ]
