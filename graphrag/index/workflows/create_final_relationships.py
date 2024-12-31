# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_relationships import (
    create_final_relationships,
)
from graphrag.index.operations.snapshot import snapshot

workflow_name = "create_final_relationships"


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final relationships."""
    base_relationship_edges = await context.runtime_storage.get(
        "base_relationship_edges"
    )

    output = create_final_relationships(base_relationship_edges)

    await snapshot(
        output,
        name="create_final_relationships",
        storage=context.storage,
        formats=["parquet"],
    )

    return output
