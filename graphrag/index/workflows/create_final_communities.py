# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_communities import (
    create_final_communities,
)
from graphrag.index.operations.snapshot import snapshot

workflow_name = "create_final_communities"


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final communities."""
    base_entity_nodes = await context.runtime_storage.get("base_entity_nodes")
    base_relationship_edges = await context.runtime_storage.get(
        "base_relationship_edges"
    )
    base_communities = await context.runtime_storage.get("base_communities")
    output = create_final_communities(
        base_entity_nodes,
        base_relationship_edges,
        base_communities,
    )

    await snapshot(
        output,
        name="create_final_communities",
        storage=context.storage,
        formats=["parquet"],
    )

    return output
