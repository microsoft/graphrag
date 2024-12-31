# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_text_units import (
    create_final_text_units,
)
from graphrag.index.operations.snapshot import snapshot
from graphrag.utils.storage import load_table_from_storage

workflow_name = "create_final_text_units"


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform the text units."""
    text_units = await context.runtime_storage.get("base_text_units")
    final_entities = await load_table_from_storage(
        "create_final_entities.parquet", context.storage
    )
    final_relationships = await load_table_from_storage(
        "create_final_relationships.parquet", context.storage
    )
    final_covariates = await load_table_from_storage(
        "create_final_covariates.parquet", context.storage
    )

    output = create_final_text_units(
        text_units,
        final_entities,
        final_relationships,
        final_covariates,
    )

    await snapshot(
        output,
        name="create_final_text_units",
        storage=context.storage,
        formats=["parquet"],
    )

    return output
