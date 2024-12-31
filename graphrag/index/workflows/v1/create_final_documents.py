# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_documents import (
    create_final_documents,
)
from graphrag.index.operations.snapshot import snapshot

workflow_name = "create_final_documents"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform final documents."""
    documents = await context.runtime_storage.get("input")
    text_units = await context.runtime_storage.get("base_text_units")

    input = config.input
    output = create_final_documents(
        documents, text_units, input.document_attribute_columns
    )

    await snapshot(
        output,
        name="create_final_documents",
        storage=context.storage,
        formats=["parquet"],
    )

    return output
