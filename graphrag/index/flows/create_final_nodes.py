# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final nodes."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.index.operations.compute_degree import compute_degree
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.embed_graph.embed_graph import embed_graph
from graphrag.index.operations.layout_graph.layout_graph import layout_graph


def create_final_nodes(
    base_entity_nodes: pd.DataFrame,
    base_relationship_edges: pd.DataFrame,
    base_communities: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    embed_config: EmbedGraphConfig,
    layout_enabled: bool,
) -> pd.DataFrame:
    """All the steps to transform final nodes."""
    graph = create_graph(base_relationship_edges)
    graph_embeddings = None
    if embed_config.enabled:
        graph_embeddings = embed_graph(
            graph,
            embed_config,
        )
    layout = layout_graph(
        graph,
        callbacks,
        layout_enabled,
        embeddings=graph_embeddings,
    )

    degrees = compute_degree(graph)

    nodes = (
        base_entity_nodes.merge(layout, left_on="title", right_on="label", how="left")
        .merge(degrees, on="title", how="left")
        .merge(base_communities, on="title", how="left")
    )
    nodes["level"] = nodes["level"].fillna(0).astype(int)
    nodes["community"] = nodes["community"].fillna(-1).astype(int)
    # disconnected nodes and those with no community even at level 0 can be missing degree
    nodes["degree"] = nodes["degree"].fillna(0).astype(int)
    return nodes.loc[
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
