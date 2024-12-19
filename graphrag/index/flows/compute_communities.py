# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to create the base entity graph."""

from typing import Any

import pandas as pd

from graphrag.index.operations.cluster_graph import cluster_graph
from graphrag.index.operations.create_graph import create_graph


def compute_communities(
    base_relationship_edges: pd.DataFrame,
    clustering_strategy: dict[str, Any],
) -> pd.DataFrame:
    """All the steps to create the base entity graph."""
    graph = create_graph(base_relationship_edges)

    communities = cluster_graph(
        graph,
        strategy=clustering_strategy,
    )

    base_communities = pd.DataFrame(
        communities, columns=pd.Index(["level", "community", "parent", "title"])
    ).explode("title")
    base_communities["community"] = base_communities["community"].astype(int)

    return base_communities
