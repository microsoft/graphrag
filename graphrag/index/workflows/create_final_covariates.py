# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_covariates import (
    create_final_covariates,
)
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "create_final_covariates"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> pd.DataFrame | None:
    """All the steps to extract and format covariates."""
    text_units = await load_table_from_storage(
        "create_base_text_units", context.storage
    )

    claim_extraction_llm_settings = config.get_language_model_config(
        config.claim_extraction.model_id
    )
    extraction_strategy = config.claim_extraction.resolved_strategy(
        config.root_dir, claim_extraction_llm_settings
    )

    async_mode = claim_extraction_llm_settings.async_mode
    num_threads = claim_extraction_llm_settings.parallelization_num_threads

    output = await create_final_covariates(
        text_units,
        callbacks,
        context.cache,
        "claim",
        extraction_strategy,
        async_mode=async_mode,
        entity_types=None,
        num_threads=num_threads,
    )

    await write_table_to_storage(output, workflow_name, context.storage)

    return output
