# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph, _get_node_attributes, _get_edge_attributes and _get_attribute_column_mapping methods definition."""

from typing import Any

import networkx as nx
import pandas as pd
from datashaper import TableContainer, VerbCallbacks, VerbInput, progress_iterable, verb

from graphrag.index.utils import clean_str

DEFAULT_NODE_ATTRIBUTES = ["label", "type", "id", "name", "description", "community"]
DEFAULT_EDGE_ATTRIBUTES = ["label", "type", "name", "source", "target"]


@verb(name="create_graph")
def create_graph(
    input: VerbInput,
    callbacks: VerbCallbacks,
    to: str,
    type: str,  # noqa A002
    graph_type: str = "undirected",
    **kwargs,
) -> TableContainer:
    """
    Create a graph from a dataframe. The verb outputs a new column containing the graph.

    > Note: This will roll up all rows into a single graph.

    ## Usage
    ```yaml
    verb: create_graph
    args:
        type: node # The type of graph to create, one of: node, edge
        to: <column name> # The name of the column to output the graph to, this will be a graphml graph
        attributes: # The attributes for the nodes / edges
            # If using the node type, the following attributes are required:
            id: <id_column_name>

            # If using the edge type, the following attributes are required:
            source: <source_column_name>
            target: <target_column_name>

            # Other attributes can be added as follows:
            <attribute_name>: <column_name>
            ... for each attribute
    ```
    """
    if type != "node" and type != "edge":
        msg = f"Unknown type {type}"
        raise ValueError(msg)

    input_df = input.get_input()
    num_total = len(input_df)
    out_graph: nx.Graph = _create_nx_graph(graph_type)

    in_attributes = (
        _get_node_attributes(kwargs) if type == "node" else _get_edge_attributes(kwargs)
    )

    # At this point, _get_node_attributes and _get_edge_attributes have already validated
    id_col = in_attributes.get(
        "id", in_attributes.get("label", in_attributes.get("name", None))
    )
    source_col = in_attributes.get("source", None)
    target_col = in_attributes.get("target", None)

    for _, row in progress_iterable(input_df.iterrows(), callbacks.progress, num_total):
        item_attributes = {
            clean_str(key): _clean_value(row[value])
            for key, value in in_attributes.items()
            if value in row
        }
        if type == "node":
            id = clean_str(row[id_col])
            out_graph.add_node(id, **item_attributes)
        elif type == "edge":
            source = clean_str(row[source_col])
            target = clean_str(row[target_col])
            out_graph.add_edge(source, target, **item_attributes)

    graphml_string = "".join(nx.generate_graphml(out_graph))
    output_df = pd.DataFrame([{to: graphml_string}])
    return TableContainer(table=output_df)


def _clean_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return clean_str(value)

    msg = f"Value must be a string or None, got {type(value)}"
    raise TypeError(msg)


def _get_node_attributes(args: dict[str, Any]) -> dict[str, Any]:
    mapping = _get_attribute_column_mapping(
        args.get("attributes", DEFAULT_NODE_ATTRIBUTES)
    )
    if "id" not in mapping and "label" not in mapping and "name" not in mapping:
        msg = "You must specify an id, label, or name column in the node attributes"
        raise ValueError(msg)
    return mapping


def _get_edge_attributes(args: dict[str, Any]) -> dict[str, Any]:
    mapping = _get_attribute_column_mapping(
        args.get("attributes", DEFAULT_EDGE_ATTRIBUTES)
    )
    if "source" not in mapping or "target" not in mapping:
        msg = "You must specify a source and target column in the edge attributes"
        raise ValueError(msg)
    return mapping


def _get_attribute_column_mapping(
    in_attributes: dict[str, Any] | list[str],
) -> dict[str, str]:
    # Its already a attribute: column dict
    if isinstance(in_attributes, dict):
        return {
            **in_attributes,
        }

    return {attrib: attrib for attrib in in_attributes}


def _create_nx_graph(graph_type: str) -> nx.Graph:
    if graph_type == "directed":
        return nx.DiGraph()

    return nx.Graph()
