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
        .rename(columns={"label": "title"})
        .loc[
            :,
            [
                "id",
                "title",
                "type",
                "description",
                "human_readable_id",
                "source_id",
            ],
        ]
        .drop_duplicates(subset="id")
    )

    nodes = nodes.loc[nodes["title"].notna()]

    nodes["text_unit_ids"] = nodes["source_id"].str.split(",")

    return nodes.loc[
        :,
        [
            "id",
            "human_readable_id",
            "title",
            "type",
            "description",
            "text_unit_ids",
        ],
    ]
