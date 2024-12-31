# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.compute_communities import compute_communities
from graphrag.index.operations.snapshot import snapshot

workflow_name = "compute_communities"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to create the base communities."""
    base_relationship_edges = await context.runtime_storage.get(
        "base_relationship_edges"
    )

    max_cluster_size = config.cluster_graph.max_cluster_size
    use_lcc = config.cluster_graph.use_lcc
    seed = config.cluster_graph.seed

    base_communities = compute_communities(
        base_relationship_edges,
        max_cluster_size=max_cluster_size,
        use_lcc=use_lcc,
        seed=seed,
    )

    await context.runtime_storage.set("base_communities", base_communities)

    if config.snapshots.transient:
        await snapshot(
            base_communities,
            name="base_communities",
            storage=context.storage,
            formats=["parquet"],
        )

    return base_communities
