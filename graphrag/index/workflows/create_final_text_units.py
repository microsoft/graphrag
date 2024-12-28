# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.verb_callbacks import VerbCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_text_units import (
    create_final_text_units,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_final_text_units"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to transform the text units."""
    text_units = await load_table_from_storage(
        "create_base_text_units", context.storage
    )
    final_entities = await load_table_from_storage(
        "create_final_entities", context.storage
    )
    final_relationships = await load_table_from_storage(
        "create_final_relationships", context.storage
    )
    final_covariates = None
    if config.claim_extraction.enabled:
        final_covariates = await load_table_from_storage(
            "create_final_covariates", context.storage
        )

    output = create_final_text_units(
        text_units,
        final_entities,
        final_relationships,
        final_covariates,
    )

    await write_table_to_storage(output, workflow_name, context.storage)

    return output
