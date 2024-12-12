# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import Any, cast

from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_covariates import (
    create_final_covariates,
)
from graphrag.storage.pipeline_storage import PipelineStorage

workflow_name = "create_final_covariates"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final covariates table.

    ## Dependencies
    * `workflow:create_base_text_units`
    """
    claim_extract_config = config.get("claim_extract", {})
    extraction_strategy = claim_extract_config.get("strategy")
    async_mode = claim_extract_config.get("async_mode", AsyncType.AsyncIO)
    num_threads = claim_extract_config.get("num_threads")

    return [
        {
            "verb": workflow_name,
            "args": {
                "covariate_type": "claim",
                "extraction_strategy": extraction_strategy,
                "async_mode": async_mode,
                "num_threads": num_threads,
            },
            "input": {"source": "workflow:create_base_text_units"},
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    runtime_storage: PipelineStorage,
    covariate_type: str,
    extraction_strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    num_threads: int = 4,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to extract and format covariates."""
    text_units = await runtime_storage.get("base_text_units")

    output = await create_final_covariates(
        text_units,
        callbacks,
        cache,
        covariate_type,
        extraction_strategy,
        async_mode=async_mode,
        entity_types=entity_types,
        num_threads=num_threads,
    )

    return create_verb_result(cast("Table", output))
