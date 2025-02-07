# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_text_units import (
    create_final_text_units,
)
from graphrag.utils.storage import (
    load_table_from_storage,
    storage_has_table,
    write_table_to_storage,
)

workflow_name = "create_final_text_units"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform the text units."""
    text_units = await load_table_from_storage("text_units", context.storage)
    final_entities = await load_table_from_storage("entities", context.storage)
    final_relationships = await load_table_from_storage(
        "relationships", context.storage
    )
    final_covariates = None
    if config.extract_claims.enabled and await storage_has_table(
        "covariates", context.storage
    ):
        final_covariates = await load_table_from_storage("covariates", context.storage)

    output = create_final_text_units(
        text_units,
        final_entities,
        final_relationships,
        final_covariates,
    )

    await write_table_to_storage(output, "text_units", context.storage)

    return output
