# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

import pandas as pd

from graphrag.index.operations.compute_degree import compute_degree
from graphrag.index.operations.compute_edge_combined_degree import (
    compute_edge_combined_degree,
)
from graphrag.index.operations.create_graph import create_graph


def create_final_relationships(
    base_relationship_edges: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to transform final relationships."""
    relationships = base_relationship_edges

    graph = create_graph(base_relationship_edges)
    degrees = compute_degree(graph)

    relationships["combined_degree"] = compute_edge_combined_degree(
        relationships,
        degrees,
        node_name_column="title",
        node_degree_column="degree",
        edge_source_column="source",
        edge_target_column="target",
    )

    return relationships.loc[
        :,
        [
            "id",
            "human_readable_id",
            "source",
            "target",
            "description",
            "weight",
            "combined_degree",
            "text_unit_ids",
        ],
    ]
