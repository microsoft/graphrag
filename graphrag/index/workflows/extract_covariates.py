# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

from typing import Any
from uuid import uuid4

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import COVARIATES_FINAL_COLUMNS
from graphrag.index.operations.extract_covariates.extract_covariates import (
    extract_covariates as extractor,
)
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
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
        context.callbacks,
        context.cache,
        "claim",
        extraction_strategy,
        async_mode=async_mode,
        entity_types=None,
        num_threads=num_threads,
    )

    await write_table_to_storage(output, "covariates", context.storage)

    return WorkflowFunctionOutput(result=output)


async def extract_covariates(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    covariate_type: str,
    extraction_strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to extract and format covariates."""
    # reassign the id because it will be overwritten in the output by a covariate one
    # this also results in text_unit_id being copied to the output covariate table
    text_units["text_unit_id"] = text_units["id"]
    covariates = await extractor(
        input=text_units,
        callbacks=callbacks,
        cache=cache,
        column="text",
        covariate_type=covariate_type,
        strategy=extraction_strategy,
        async_mode=async_mode,
        entity_types=entity_types,
        num_threads=num_threads,
    )
    text_units.drop(columns=["text_unit_id"], inplace=True)  # don't pollute the global
    covariates["id"] = covariates["covariate_type"].apply(lambda _x: str(uuid4()))
    covariates["human_readable_id"] = covariates.index + 1

    return covariates.loc[:, COVARIATES_FINAL_COLUMNS]
