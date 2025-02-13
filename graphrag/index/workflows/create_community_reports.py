# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_community_reports import (
    create_community_reports,
)
from graphrag.index.typing import WorkflowFunctionOutput
from graphrag.utils.storage import (
    load_table_from_storage,
    storage_has_table,
    write_table_to_storage,
)

workflow_name = "create_community_reports"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: WorkflowCallbacks,
) -> WorkflowFunctionOutput:
    """All the steps to transform community reports."""
    edges = await load_table_from_storage("relationships", context.storage)
    entities = await load_table_from_storage("entities", context.storage)
    communities = await load_table_from_storage("communities", context.storage)
    claims = None
    if config.extract_claims.enabled and await storage_has_table(
        "covariates", context.storage
    ):
        claims = await load_table_from_storage("covariates", context.storage)

    community_reports_llm_settings = config.get_language_model_config(
        config.community_reports.model_id
    )
    async_mode = community_reports_llm_settings.async_mode
    num_threads = community_reports_llm_settings.concurrent_requests
    summarization_strategy = config.community_reports.resolved_strategy(
        config.root_dir, community_reports_llm_settings
    )

    output = await create_community_reports(
        edges_input=edges,
        entities=entities,
        communities=communities,
        claims_input=claims,
        callbacks=callbacks,
        cache=context.cache,
        summarization_strategy=summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    await write_table_to_storage(output, "community_reports", context.storage)

    return WorkflowFunctionOutput(result=output, config=None)
