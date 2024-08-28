# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing merge_graphs, merge_nodes, merge_edges, merge_attributes, apply_merge_operation and _get_detailed_attribute_merge_operation methods definitions."""

from typing import Any, cast

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, progress_iterable, verb

from graphrag.index.utils import load_graph

from .defaults import (
    DEFAULT_CONCAT_SEPARATOR,
    DEFAULT_EDGE_OPERATIONS,
    DEFAULT_NODE_OPERATIONS,
)
from .typing import (
    BasicMergeOperation,
    DetailedAttributeMergeOperation,
    NumericOperation,
    StringOperation,
)


@verb(name="merge_graphs")
def merge_graphs(
    input: VerbInput,
    callbacks: VerbCallbacks,
    column: str,
    to: str,
    nodes: dict[str, Any] = DEFAULT_NODE_OPERATIONS,
    edges: dict[str, Any] = DEFAULT_EDGE_OPERATIONS,
    **_kwargs,
) -> TableContainer:
    """
    Merge multiple graphs together. The graphs are expected to be in graphml format. The verb outputs a new column containing the merged graph.

    > Note: This will merge all rows into a single graph.

    ## Usage
    ```yaml
    verb: merge_graph
    args:
        column: clustered_graph # The name of the column containing the graph, should be a graphml graph
        to: merged_graph # The name of the column to output the merged graph to
        nodes: <node operations> # See node operations section below
        edges: <edge operations> # See edge operations section below
    ```

    ## Node Operations
    The merge graph verb can perform operations on the nodes of the graph.

    ### Usage
    ```yaml
    nodes:
        <attribute name>: <operation>
        ... for each attribute or use the special value "*" for all attributes
    ```

    ## Edge Operations
    The merge graph verb can perform operations on the nodes of the graph.

    ### Usage
    ```yaml
    edges:
        <attribute name>: <operation>
        ... for each attribute or use the special value "*" for all attributes
    ```

    ## Operations
    The merge graph verb can perform operations on the nodes and edges of the graph. The following operations are available:

    - __replace__: This operation replaces the attribute with the last value seen.
    - __skip__: This operation skips the attribute, and just uses the first value seen.
    - __concat__: This operation concatenates the attribute with the last value seen.
    - __sum__: This operation sums the attribute with the last value seen.
    - __max__: This operation takes the max of the attribute with the last value seen.
    max
    - __min__: This operation takes the min of the attribute with the last value seen.
    - __average__: This operation takes the mean of the attribute with the last value seen.
    - __multiply__: This operation multiplies the attribute with the last value seen.
    """
    input_df = input.get_input()
    output = pd.DataFrame()

    node_ops = {
        attrib: _get_detailed_attribute_merge_operation(value)
        for attrib, value in nodes.items()
    }
    edge_ops = {
        attrib: _get_detailed_attribute_merge_operation(value)
        for attrib, value in edges.items()
    }

    mega_graph = nx.Graph()
    num_total = len(input_df)
    for graphml in progress_iterable(input_df[column], callbacks.progress, num_total):
        graph = load_graph(cast(str | nx.Graph, graphml))
        merge_nodes(mega_graph, graph, node_ops)
        merge_edges(mega_graph, graph, edge_ops)

    output[to] = ["\n".join(nx.generate_graphml(mega_graph))]

    return TableContainer(table=output)


def merge_nodes(
    target: nx.Graph,
    subgraph: nx.Graph,
    node_ops: dict[str, DetailedAttributeMergeOperation],
):
    """Merge nodes from subgraph into target using the operations defined in node_ops."""
    for node in subgraph.nodes:
        if node not in target.nodes:
            target.add_node(node, **(subgraph.nodes[node] or {}))
        else:
            merge_attributes(target.nodes[node], subgraph.nodes[node], node_ops)


def merge_edges(
    target_graph: nx.Graph,
    subgraph: nx.Graph,
    edge_ops: dict[str, DetailedAttributeMergeOperation],
):
    """Merge edges from subgraph into target using the operations defined in edge_ops."""
    for source, target, edge_data in subgraph.edges(data=True):  # type: ignore
        if not target_graph.has_edge(source, target):
            target_graph.add_edge(source, target, **(edge_data or {}))
        else:
            merge_attributes(
                target_graph.edges[(source, target)],  # noqa
                edge_data,
                edge_ops,
            )


def merge_attributes(
    target_item: dict[str, Any] | None,
    source_item: dict[str, Any] | None,
    ops: dict[str, DetailedAttributeMergeOperation],
):
    """Merge attributes from source_item into target_item using the operations defined in ops."""
    source_item = source_item or {}
    target_item = target_item or {}
    for op_attrib, op in ops.items():
        if op_attrib == "*":
            for attrib in source_item:
                # If there is a specific handler for this attribute, use it
                # i.e. * provides a default, but you can override it
                if attrib not in ops:
                    apply_merge_operation(target_item, source_item, attrib, op)
        else:
            if op_attrib in source_item or op_attrib in target_item:
                apply_merge_operation(target_item, source_item, op_attrib, op)


def apply_merge_operation(
    target_item: dict[str, Any] | None,
    source_item: dict[str, Any] | None,
    attrib: str,
    op: DetailedAttributeMergeOperation,
):
    """Apply the merge operation to the attribute."""
    source_item = source_item or {}
    target_item = target_item or {}

    if (
        op.operation == BasicMergeOperation.Replace
        or op.operation == StringOperation.Replace
    ):
        target_item[attrib] = source_item.get(attrib, None) or ""
    elif (
        op.operation == BasicMergeOperation.Skip or op.operation == StringOperation.Skip
    ):
        target_item[attrib] = target_item.get(attrib, None) or ""
    elif op.operation == StringOperation.Concat:
        separator = op.separator or DEFAULT_CONCAT_SEPARATOR
        target_attrib = target_item.get(attrib, "") or ""
        source_attrib = source_item.get(attrib, "") or ""
        target_item[attrib] = f"{target_attrib}{separator}{source_attrib}"
        if op.distinct:
            # TODO: Slow
            target_item[attrib] = separator.join(
                sorted(set(target_item[attrib].split(separator)))
            )

    # We're assuming that the attribute is numeric
    elif op.operation == NumericOperation.Sum:
        target_item[attrib] = (target_item.get(attrib, 0) or 0) + (
            source_item.get(attrib, 0) or 0
        )
    elif op.operation == NumericOperation.Average:
        target_item[attrib] = (
            (target_item.get(attrib, 0) or 0) + (source_item.get(attrib, 0) or 0)
        ) / 2
    elif op.operation == NumericOperation.Max:
        target_item[attrib] = max(
            (target_item.get(attrib, 0) or 0), (source_item.get(attrib, 0) or 0)
        )
    elif op.operation == NumericOperation.Min:
        target_item[attrib] = min(
            (target_item.get(attrib, 0) or 0), (source_item.get(attrib, 0) or 0)
        )
    elif op.operation == NumericOperation.Multiply:
        target_item[attrib] = (target_item.get(attrib, 1) or 1) * (
            source_item.get(attrib, 1) or 1
        )
    else:
        msg = f"Invalid operation {op.operation}"
        raise ValueError(msg)


def _get_detailed_attribute_merge_operation(
    value: str | dict[str, Any],
) -> DetailedAttributeMergeOperation:
    """Normalize the AttributeMergeOperation into a DetailedAttributeMergeOperation."""
    if isinstance(value, str):
        return DetailedAttributeMergeOperation(operation=value)
    return DetailedAttributeMergeOperation(**value)
