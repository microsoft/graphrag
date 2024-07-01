# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph, _get_node_attributes, _get_edge_attributes and _get_attribute_column_mapping methods definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from graphrag.index.graph.extractors.community_reports.schemas import (
    NODE_DEGREE,
    NODE_DESCRIPTION,
    NODE_DETAILS,
    NODE_ID,
    NODE_NAME,
)

_MISSING_DESCRIPTION = "No Description"


@verb(name="prepare_community_reports_nodes")
def prepare_community_reports_nodes(
    input: VerbInput,
    to: str = NODE_DETAILS,
    id_column: str = NODE_ID,
    name_column: str = NODE_NAME,
    description_column: str = NODE_DESCRIPTION,
    degree_column: str = NODE_DEGREE,
    **_kwargs,
) -> TableContainer:
    """Merge edge details into an object."""
    node_df = cast(pd.DataFrame, input.get_input())
    node_df = node_df.fillna(value={description_column: _MISSING_DESCRIPTION})

    # merge values of four columns into a map column
    node_df[to] = node_df.apply(
        lambda x: {
            id_column: x[id_column],
            name_column: x[name_column],
            description_column: x[description_column],
            degree_column: x[degree_column],
        },
        axis=1,
    )
    return TableContainer(table=node_df)
