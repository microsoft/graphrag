# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships before they are embedded."""

from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.verbs.graph.unpack import unpack_graph_df


@verb(
    name="create_final_relationships_pre_embedding",
    treats_input_tables_as_immutable=True,
)
def create_final_relationships_pre_embedding(
    input: VerbInput,
    callbacks: VerbCallbacks,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final relationships before they are embedded."""
    table = cast(pd.DataFrame, input.get_input())

    graph_edges = unpack_graph_df(table, callbacks, "clustered_graph", "edges")

    graph_edges.rename(columns={"source_id": "text_unit_ids"}, inplace=True)

    filtered = graph_edges[graph_edges["level"] == 0].reset_index(drop=True)

    return create_verb_result(cast(Table, filtered))
