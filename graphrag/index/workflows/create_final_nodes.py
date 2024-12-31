# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_nodes import (
    create_final_nodes,
)
from graphrag.index.operations.snapshot import snapshot

workflow_name = "create_final_nodes"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final nodes."""
    base_entity_nodes = await context.runtime_storage.get("base_entity_nodes")
    base_relationship_edges = await context.runtime_storage.get(
        "base_relationship_edges"
    )
    base_communities = await context.runtime_storage.get("base_communities")

    embed_config = config.embed_graph
    layout_enabled = config.umap.enabled

    output = create_final_nodes(
        base_entity_nodes,
        base_relationship_edges,
        base_communities,
        callbacks,
        embed_config=embed_config,
        layout_enabled=layout_enabled,
    )
    await snapshot(
        output,
        name="create_final_nodes",
        storage=context.storage,
        formats=["parquet"],
    )

    return output
