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
from graphrag.index.verbs.overrides.aggregate import aggregate_df


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

    source_clusters = graph_nodes.merge(
        graph_edges,
        left_on="label",
        right_on="source",
        how="inner",
    )
    target_clusters = graph_nodes.merge(
        graph_edges,
        left_on="label",
        right_on="target",
        how="inner",
    )

    concatenated_clusters = pd.concat(
        [source_clusters, target_clusters], ignore_index=True
    )

    # level_x is the left side of the join
    # level_y is the right side of the join
    # we only want to keep the clusters that are the same on both sides
    combined_clusters = concatenated_clusters[
        concatenated_clusters["level_x"] == concatenated_clusters["level_y"]
    ].reset_index(drop=True)

    cluster_relationships = aggregate_df(
        cast(Table, combined_clusters),
        aggregations=[
            {
                "column": "id_y",  # this is the id of the edge from the join steps above
                "to": "relationship_ids",
                "operation": "array_agg_distinct",
            },
            {
                "column": "source_id_x",
                "to": "text_unit_ids",
                "operation": "array_agg_distinct",
            },
        ],
        groupby=[
            "cluster",
            "level_x",  # level_x is the left side of the join
        ],
    )

    all_clusters = aggregate_df(
        graph_nodes,
        aggregations=[{"column": "cluster", "to": "id", "operation": "any"}],
        groupby=["cluster", "level"],
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
            filtered[
                [
                    "id",
                    "title",
                    "level",
                    "relationship_ids",
                    "text_unit_ids",
                ]
            ],
        )
    )
