# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_base_text_units import (
    create_base_text_units,
)
from graphrag.index.operations.snapshot import snapshot

workflow_name = "create_base_text_units"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform base text_units."""
    documents = await context.runtime_storage.get("input")

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

    await context.runtime_storage.set("create_base_text_units", output)

    if config.snapshots.transient:
        await snapshot(
            output,
            name="create_base_text_units",
            storage=context.storage,
            formats=["parquet"],
        )

    return output
