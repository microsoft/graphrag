# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_base_text_units import (
    create_base_text_units,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_base_text_units"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform base text_units."""
    documents = await load_table_from_storage("documents", context.storage)

    chunks = config.chunks

    output = create_base_text_units(
        documents,
        callbacks,
        chunks.group_by_columns,
        chunks.size,
        chunks.overlap,
        chunks.encoding_model,
        strategy=chunks.strategy,
    )

    await write_table_to_storage(output, "text_units", context.storage)

    return output
