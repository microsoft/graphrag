# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final communities."""

from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.operations.unpack_graph import unpack_graph


def create_final_communities(
    entity_graph: pd.DataFrame,
    callbacks: VerbCallbacks,
) -> pd.DataFrame:
    """All the steps to transform final communities."""
    graph_nodes = unpack_graph(entity_graph, callbacks, "clustered_graph", "nodes")
    graph_edges = unpack_graph(entity_graph, callbacks, "clustered_graph", "edges")

    # Merge graph_nodes with graph_edges for both source and target matches
    source_clusters = graph_nodes.merge(
        graph_edges, left_on="label", right_on="source", how="inner"
    )

    target_clusters = graph_nodes.merge(
        graph_edges, left_on="label", right_on="target", how="inner"
    )

    # Concatenate the source and target clusters
    clusters = pd.concat([source_clusters, target_clusters], ignore_index=True)

    # Keep only rows where level_x == level_y
    combined_clusters = clusters[
        clusters["level_x"] == clusters["level_y"]
    ].reset_index(drop=True)

    cluster_relationships = (
        combined_clusters.groupby(["cluster", "level_x"], sort=False)
        .agg(
            relationship_ids=("id_y", "unique"),
            text_unit_ids=("source_id_x", "unique"),
            entity_ids=("id_x", "unique"),
        )
        .reset_index()
    )

    all_clusters = (
        graph_nodes.groupby(["cluster", "level"], sort=False)
        .agg(community=("cluster", "first"))
        .reset_index()
    )

    joined = all_clusters.merge(
        cluster_relationships,
        left_on="community",
        right_on="cluster",
        how="inner",
    )

    filtered = cast(
        pd.DataFrame,
        joined[joined["level"] == joined["level_x"]].reset_index(drop=True),
    )

    filtered["id"] = filtered["community"].apply(lambda _x: str(uuid4()))
    filtered["community"] = filtered["community"].astype(int)
    filtered["human_readable_id"] = filtered["community"]
    filtered["title"] = "Community " + filtered["community"].astype(str)

    # Add period timestamp to the community reports
    filtered["period"] = datetime.now(timezone.utc).date().isoformat()

    # Add size of the community
    filtered["size"] = filtered.loc[:, "entity_ids"].apply(lambda x: len(x))

    return filtered.loc[
        :,
        [
            "id",
            "human_readable_id",
            "community",
            "level",
            "title",
            "entity_ids",
            "relationship_ids",
            "text_unit_ids",
            "period",
            "size",
        ],
    ]
