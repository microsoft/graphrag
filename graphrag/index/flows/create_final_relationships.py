# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

from typing import cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.compute_edge_combined_degree import (
    compute_edge_combined_degree,
)
from graphrag.index.operations.embed_text import embed_text
from graphrag.index.operations.unpack_graph import unpack_graph


async def create_final_relationships(
    entity_graph: pd.DataFrame,
    nodes: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    description_text_embed: dict | None = None,
) -> pd.DataFrame:
    """All the steps to transform final relationships."""
    graph_edges = unpack_graph(entity_graph, callbacks, "clustered_graph", "edges")

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

    pruned_edges["rank"] = compute_edge_combined_degree(
        pruned_edges,
        filtered_nodes,
        node_name_column="title",
        node_degree_column="degree",
        edge_source_column="source",
        edge_target_column="target",
    )

    pruned_edges["human_readable_id"] = pruned_edges[
        "human_readable_id"
    ].astype(str)
    pruned_edges["text_unit_ids"] = pruned_edges[
        "text_unit_ids"
    ].str.split(",")

    # TODO: Find duplication source
    return pruned_edges.drop_duplicates(subset=["source", "target"])
