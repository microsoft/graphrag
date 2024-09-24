# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final communities."""

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


@verb(name="create_final_communities", treats_input_tables_as_immutable=True)
def create_final_communities(
    input: VerbInput,
    callbacks: VerbCallbacks,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final communities."""
    table = cast(pd.DataFrame, input.get_input())

    graph_nodes = unpack_graph_df(table, callbacks, "clustered_graph", "nodes")
    graph_edges = unpack_graph_df(table, callbacks, "clustered_graph", "edges")

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
            relationship_ids=("id_y", "unique"), text_unit_ids=("source_id_x", "unique")
        )
        .reset_index()
    )

    all_clusters = (
        graph_nodes.groupby(["cluster", "level"], sort=False)
        .agg(id=("cluster", "first"))
        .reset_index()
    )

    joined = all_clusters.merge(
        cluster_relationships,
        left_on="id",
        right_on="cluster",
        how="inner",
    )

    filtered = joined[joined["level"] == joined["level_x"]].reset_index(drop=True)

    filtered["title"] = "Community " + filtered["id"].astype(str)

    return create_verb_result(
        cast(
            Table,
            filtered.loc[
                :,
                [
                    "id",
                    "title",
                    "level",
                    "relationship_ids",
                    "text_unit_ids",
                ],
            ],
        )
    )
