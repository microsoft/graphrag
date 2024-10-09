# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

from typing import cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.index.verbs.graph.compute_edge_combined_degree import (
    compute_edge_combined_degree_df,
)
from graphrag.index.verbs.graph.unpack import unpack_graph_df


async def create_final_relationships(
    entity_graph: pd.DataFrame,
    nodes: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    description_text_embed: dict | None = None,
) -> pd.DataFrame:
    """All the steps to transform final relationships."""
    graph_edges = unpack_graph_df(entity_graph, callbacks, "clustered_graph", "edges")

    graph_edges.rename(columns={"source_id": "text_unit_ids"}, inplace=True)

    filtered = cast(
        pd.DataFrame, graph_edges[graph_edges["level"] == 0].reset_index(drop=True)
    )

    if description_text_embed:
        filtered["description_embedding"] = await embed_text(
            filtered,
            callbacks,
            cache,
            column="description",
            strategy=description_text_embed["strategy"],
            embedding_name="relationship_description",
        )

    pruned_edges = filtered.drop(columns=["level"])

    filtered_nodes = nodes[nodes["level"] == 0].reset_index(drop=True)
    filtered_nodes = cast(pd.DataFrame, filtered_nodes[["title", "degree"]])

    edge_combined_degree = compute_edge_combined_degree_df(
        pruned_edges,
        filtered_nodes,
        to="rank",
        node_name_column="title",
        node_degree_column="degree",
        edge_source_column="source",
        edge_target_column="target",
    )

    edge_combined_degree["human_readable_id"] = edge_combined_degree[
        "human_readable_id"
    ].astype(str)
    edge_combined_degree["text_unit_ids"] = edge_combined_degree[
        "text_unit_ids"
    ].str.split(",")

    return edge_combined_degree
