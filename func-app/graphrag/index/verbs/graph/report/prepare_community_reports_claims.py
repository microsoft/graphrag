# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_graph, _get_node_attributes, _get_edge_attributes and _get_attribute_column_mapping methods definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from graphrag.index.graph.extractors.community_reports.schemas import (
    CLAIM_DESCRIPTION,
    CLAIM_DETAILS,
    CLAIM_ID,
    CLAIM_STATUS,
    CLAIM_SUBJECT,
    CLAIM_TYPE,
)

_MISSING_DESCRIPTION = "No Description"


@verb(name="prepare_community_reports_claims")
def prepare_community_reports_claims(
    input: VerbInput,
    to: str = CLAIM_DETAILS,
    id_column: str = CLAIM_ID,
    description_column: str = CLAIM_DESCRIPTION,
    subject_column: str = CLAIM_SUBJECT,
    type_column: str = CLAIM_TYPE,
    status_column: str = CLAIM_STATUS,
    **_kwargs,
) -> TableContainer:
    """Merge claim details into an object."""
    claim_df: pd.DataFrame = cast(pd.DataFrame, input.get_input())
    claim_df = claim_df.fillna(value={description_column: _MISSING_DESCRIPTION})

    # merge values of five columns into a map column
    claim_df[to] = claim_df.apply(
        lambda x: {
            id_column: x[id_column],
            subject_column: x[subject_column],
            type_column: x[type_column],
            status_column: x[status_column],
            description_column: x[description_column],
        },
        axis=1,
    )

    return TableContainer(table=claim_df)
