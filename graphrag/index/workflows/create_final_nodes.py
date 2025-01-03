# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_nodes import (
    create_final_nodes,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_final_nodes"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final nodes."""
    base_entity_nodes = await load_table_from_storage(
        "base_entity_nodes", context.storage
    )
    base_relationship_edges = await load_table_from_storage(
        "base_relationship_edges", context.storage
    )
    base_communities = await load_table_from_storage(
        "base_communities", context.storage
    )

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

    await write_table_to_storage(output, workflow_name, context.storage)

    return output
