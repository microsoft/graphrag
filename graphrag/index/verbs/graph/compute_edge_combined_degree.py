# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_graph, _get_node_attributes, _get_edge_attributes and _get_attribute_column_mapping methods definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

_NAMED_INPUTS_REQUIRED = "Named inputs are required"
_NODES_INPUT_REQUIRED = "Nodes input is required"


@verb(name="compute_edge_combined_degree")
def compute_edge_combined_degree(
    input: VerbInput,
    to: str = "rank",
    node_name_column: str = "title",
    node_degree_column: str = "degree",
    edge_source_column: str = "source",
    edge_target_column: str = "target",
    **_kwargs,
) -> TableContainer:
    """
    Compute the combined degree for each edge in a graph.

    Inputs Tables:
    - input: The edge table
    - nodes: The nodes table.

    Args:
    - to: The name of the column to output the combined degree to. Default="rank"
    """
    edge_df: pd.DataFrame = cast(pd.DataFrame, input.get_input())
    if to in edge_df.columns:
        return TableContainer(table=edge_df)
    node_df = _get_nodes_table(input)

    node_degree_df = cast(pd.DataFrame, node_df[[node_name_column, node_degree_column]])
    combined_degree_df = edge_df.merge(
        node_degree_df.rename(
            columns={
                node_name_column: edge_source_column,
                node_degree_column: f"{edge_source_column}_degree",
            }
        ),
        on=edge_source_column,
        how="left",
    )
    combined_degree_df = combined_degree_df.merge(
        node_degree_df.rename(
            columns={
                node_name_column: edge_target_column,
                node_degree_column: f"{edge_target_column}_degree",
            }
        ),
        on=edge_target_column,
        how="left",
    )
    combined_degree_df[f"{edge_source_column}_degree"] = combined_degree_df[
        f"{edge_source_column}_degree"
    ].fillna(0)
    combined_degree_df[f"{edge_target_column}_degree"] = combined_degree_df[
        f"{edge_target_column}_degree"
    ].fillna(0)
    combined_degree_df[to] = (
        combined_degree_df[f"{edge_source_column}_degree"]
        + combined_degree_df[f"{edge_target_column}_degree"]
    )

    return TableContainer(table=combined_degree_df)


def _get_nodes_table(input: VerbInput) -> pd.DataFrame:
    named_inputs = input.named
    if named_inputs is None:
        raise ValueError(_NAMED_INPUTS_REQUIRED)
    nodes = named_inputs.get("nodes")
    if nodes is None:
        raise ValueError(_NODES_INPUT_REQUIRED)
    return cast(pd.DataFrame, nodes.table)
