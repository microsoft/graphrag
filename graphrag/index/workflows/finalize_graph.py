# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.finalize_graph import (
    finalize_graph,
)
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.index.typing import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "finalize_graph"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    entities = await load_table_from_storage("entities", context.storage)
    relationships = await load_table_from_storage("relationships", context.storage)

    final_entities, final_relationships = finalize_graph(
        entities,
        relationships,
        callbacks,
        embed_config=config.embed_graph,
        layout_enabled=config.umap.enabled,
    )

    await write_table_to_storage(final_entities, "entities", context.storage)
    await write_table_to_storage(final_relationships, "relationships", context.storage)

    if config.snapshots.graphml:
        # todo: extract graphs at each level, and add in meta like descriptions
        graph = create_graph(relationships)
        await snapshot_graphml(
            graph,
            name="graph",
            storage=context.storage,
        )

    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        },
        config=None,
    )
