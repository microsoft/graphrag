# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_entities import (
    create_final_entities,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_final_entities"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final entities."""
    base_entities = await load_table_from_storage("entities", context.storage)
    base_relationship_edges = await load_table_from_storage(
        "base_relationship_edges", context.storage
    )

    output = create_final_entities(
        base_entities,
        base_relationship_edges,
        callbacks,
        embed_config=config.embed_graph,
        layout_enabled=config.umap.enabled,
    )

    await write_table_to_storage(output, "entities", context.storage)

    return output
