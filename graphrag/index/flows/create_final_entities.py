# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.operations.split_text import split_text
from graphrag.index.operations.unpack_graph import unpack_graph


def create_final_entities(
    entity_graph: pd.DataFrame,
    callbacks: VerbCallbacks,
) -> pd.DataFrame:
    """All the steps to transform final entities."""
    # Process nodes
    nodes = (
        unpack_graph(entity_graph, callbacks, "clustered_graph", "nodes")
        .rename(columns={"label": "name"})
        .loc[
            :,
            [
                "id",
                "name",
                "type",
                "description",
                "human_readable_id",
                "graph_embedding",
                "source_id",
            ],
        ]
        .drop_duplicates(subset="id")
    )

    nodes = nodes.loc[nodes["name"].notna()]

    # Split 'source_id' column into 'text_unit_ids'
    return split_text(
        nodes, column="source_id", separator=",", to="text_unit_ids"
    ).drop(columns=["source_id"])
