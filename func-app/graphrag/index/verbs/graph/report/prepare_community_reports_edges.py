# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph, _get_node_attributes, _get_edge_attributes and _get_attribute_column_mapping methods definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from graphrag.index.graph.extractors.community_reports.schemas import (
    EDGE_DEGREE,
    EDGE_DESCRIPTION,
    EDGE_DETAILS,
    EDGE_ID,
    EDGE_SOURCE,
    EDGE_TARGET,
)

_MISSING_DESCRIPTION = "No Description"


@verb(name="prepare_community_reports_edges")
def prepare_community_reports_edges(
    input: VerbInput,
    to: str = EDGE_DETAILS,
    id_column: str = EDGE_ID,
    source_column: str = EDGE_SOURCE,
    target_column: str = EDGE_TARGET,
    description_column: str = EDGE_DESCRIPTION,
    degree_column: str = EDGE_DEGREE,
    **_kwargs,
) -> TableContainer:
    """Merge edge details into an object."""
    edge_df: pd.DataFrame = cast(pd.DataFrame, input.get_input()).fillna(
        value={description_column: _MISSING_DESCRIPTION}
    )
    edge_df[to] = edge_df.apply(
        lambda x: {
            id_column: x[id_column],
            source_column: x[source_column],
            target_column: x[target_column],
            description_column: x[description_column],
            degree_column: x[degree_column],
        },
        axis=1,
    )
    return TableContainer(table=edge_df)
