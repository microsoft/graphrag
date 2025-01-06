# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_communities import (
    create_final_communities,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_final_communities"


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final communities."""
    base_entity_nodes = await load_table_from_storage(
        "base_entity_nodes", context.storage
    )
    base_relationship_edges = await load_table_from_storage(
        "base_relationship_edges", context.storage
    )
    base_communities = await load_table_from_storage(
        "base_communities", context.storage
    )

    output = create_final_communities(
        base_entity_nodes,
        base_relationship_edges,
        base_communities,
    )

    await write_table_to_storage(output, workflow_name, context.storage)

    return output
