# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.verb_callbacks import VerbCallbacks
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
    callbacks: VerbCallbacks,
) -> pd.DataFrame | None:
    """All the steps to extract and format covariates."""
    text_units = await load_table_from_storage(
        "create_base_text_units", context.storage
    )

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

    await write_table_to_storage(output, workflow_name, context.storage)

    return output
