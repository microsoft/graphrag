# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any, cast

from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.flows.create_final_covariates import (
    create_final_covariates as create_final_covariates_flow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage


@verb(name="create_final_covariates", treats_input_tables_as_immutable=True)
async def create_final_covariates(
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

    output = await create_final_covariates_flow(
        text_units,
        callbacks,
        cache,
        covariate_type,
        extraction_strategy,
        async_mode=async_mode,
        entity_types=entity_types,
        num_threads=num_threads,
    )

    return create_verb_result(cast(Table, output))
