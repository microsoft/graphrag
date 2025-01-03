# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_documents import (
    create_final_documents,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_final_documents"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final documents."""
    documents = await load_table_from_storage("input", context.storage)
    text_units = await load_table_from_storage(
        "create_base_text_units", context.storage
    )

    input = config.input
    output = create_final_documents(
        documents, text_units, input.document_attribute_columns
    )

    await write_table_to_storage(output, workflow_name, context.storage)

    return output
