# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final nodes."""

from typing import Any

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.embed_graph import embed_graph
from graphrag.index.operations.layout_graph import layout_graph


def create_final_nodes(
    base_entity_nodes: pd.DataFrame,
    base_relationship_edges: pd.DataFrame,
    base_communities: pd.DataFrame,
    callbacks: VerbCallbacks,
    layout_strategy: dict[str, Any],
    embedding_strategy: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """All the steps to transform final nodes."""
    graph = create_graph(base_relationship_edges)
    graph_embeddings = None
    if embedding_strategy:
        graph_embeddings = embed_graph(
            graph,
            embedding_strategy,
        )
    layout = layout_graph(
        graph,
        callbacks,
        layout_strategy,
        embeddings=graph_embeddings,
    )
    nodes = base_entity_nodes.merge(
        layout, left_on="title", right_on="label", how="left"
    )

    joined = nodes.merge(base_communities, on="title", how="left")
    joined["level"] = joined["level"].fillna(0).astype(int)
    joined["community"] = joined["community"].fillna(-1).astype(int)

    return joined.loc[
        :,
        [
            "id",
            "human_readable_id",
            "title",
            "community",
            "level",
            "degree",
            "x",
            "y",
        ],
    ]
