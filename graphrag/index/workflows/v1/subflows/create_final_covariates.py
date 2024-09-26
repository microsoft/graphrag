# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any, cast
from uuid import uuid4

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
from graphrag.index.verbs.covariates.extract_covariates.extract_covariates import (
    extract_covariates_df,
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
    **kwargs: dict,
) -> VerbResult:
    """All the steps to extract and format covariates."""
    source = cast(pd.DataFrame, input.get_input())

    covariates = await extract_covariates_df(
        source,
        cache,
        callbacks,
        column,
        covariate_type,
        strategy,
        async_mode,
        entity_types,
        **kwargs,
    )

    covariates["id"] = covariates["covariate_type"].apply(lambda _x: str(uuid4()))
    covariates["human_readable_id"] = (covariates.index + 1).astype(str)
    covariates.rename(columns={"chunk_id": "text_unit_id"}, inplace=True)

    return create_verb_result(
        cast(
            Table,
            covariates[
                [
                    "id",
                    "human_readable_id",
                    "covariate_type",
                    "type",
                    "description",
                    "subject_id",
                    "object_id",
                    "status",
                    "start_date",
                    "end_date",
                    "source_text",
                    "text_unit_id",
                    "document_ids",
                    "n_tokens",
                ]
            ],
        )
    )
