# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.verb_callbacks import VerbCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_relationships import (
    create_final_relationships,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_final_relationships"


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final relationships."""
    base_relationship_edges = await load_table_from_storage(
        "base_relationship_edges", context.storage
    )

    output = create_final_relationships(base_relationship_edges)

    await write_table_to_storage(output, workflow_name, context.storage)

    return output
