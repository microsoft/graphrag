# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache
from graphrag.index.flows.create_final_covariates import (
    create_final_covariates as create_final_covariates_flow,
)


@verb(name="create_final_covariates", treats_input_tables_as_immutable=True)
async def create_final_covariates(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    column: str,
    covariate_type: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    num_threads: int = 4,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to extract and format covariates."""
    source = cast(pd.DataFrame, input.get_input())

    output = await create_final_covariates_flow(
        source,
        cache,
        callbacks,
        column,
        covariate_type,
        strategy,
        async_mode,
        entity_types,
        num_threads,
    )

    return create_verb_result(cast(Table, output))
