# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.extract_covariates import (
    extract_covariates,
)
from graphrag.index.typing import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

workflow_name = "extract_covariates"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> WorkflowFunctionOutput:
    """All the steps to extract and format covariates."""
    text_units = await load_table_from_storage("text_units", context.storage)

    extract_claims_llm_settings = config.get_language_model_config(
        config.extract_claims.model_id
    )
    extraction_strategy = config.extract_claims.resolved_strategy(
        config.root_dir, extract_claims_llm_settings
    )

    async_mode = extract_claims_llm_settings.async_mode
    num_threads = extract_claims_llm_settings.concurrent_requests

    output = await extract_covariates(
        text_units,
        callbacks,
        context.cache,
        "claim",
        extraction_strategy,
        async_mode=async_mode,
        entity_types=None,
        num_threads=num_threads,
    )

    await write_table_to_storage(output, "covariates", context.storage)

    return WorkflowFunctionOutput(result=output, config=None)
