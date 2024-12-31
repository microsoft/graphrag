# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.flows.create_final_covariates import (
    create_final_covariates,
)
from graphrag.index.operations.snapshot import snapshot

workflow_name = "create_final_covariates"


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
    callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to extract and format covariates."""
    text_units = await context.runtime_storage.get("create_base_text_units")

    extraction_strategy = config.claim_extraction.resolved_strategy(
        config.root_dir, config.encoding_model
    )

    async_mode = config.claim_extraction.async_mode
    num_threads = config.claim_extraction.parallelization.num_threads

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

    await snapshot(
        output,
        name="create_final_covariates",
        storage=context.storage,
        formats=["parquet"],
    )

    return output
