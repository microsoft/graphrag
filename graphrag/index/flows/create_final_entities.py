# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

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
                "source_id",
            ],
        ]
        .drop_duplicates(subset="id")
    )

    nodes = nodes.loc[nodes["name"].notna()]

    nodes["text_unit_ids"] = nodes["source_id"].str.split(",")
    nodes.drop(columns=["source_id"], inplace=True)

    return nodes
