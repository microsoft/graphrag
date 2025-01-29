# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.extract_graph_nlp import (
    extract_graph_nlp,
)
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "extract_graph_nlp"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to create the base entity graph."""
    text_units = await load_table_from_storage(
        "create_base_text_units", context.storage
    )

    base_entity_nodes, base_relationship_edges = extract_graph_nlp(
        text_units,
        extraction_config=config.extract_graph_nlp,
        pruning_config=config.prune_graph,
    )

    await write_table_to_storage(
        base_entity_nodes, "base_entity_nodes", context.storage
    )
    await write_table_to_storage(
        base_relationship_edges, "base_relationship_edges", context.storage
    )

    if config.snapshots.graphml:
        # todo: extract graphs at each level, and add in meta like descriptions
        graph = create_graph(base_relationship_edges)
        await snapshot_graphml(
            graph,
            name="graph",
            storage=context.storage,
        )
