# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any, cast
from uuid import uuid4

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.extract_covariates import (
    extract_covariates,
)


async def create_final_covariates(
    text_units: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    column: str,
    covariate_type: str,
    extraction_strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    num_threads: int = 4,
) -> pd.DataFrame:
    """All the steps to extract and format covariates."""
    covariates = await extract_covariates(
        text_units,
        callbacks,
        cache,
        column,
        covariate_type,
        extraction_strategy,
        async_mode,
        entity_types,
        num_threads,
    )

    covariates["id"] = covariates["covariate_type"].apply(lambda _x: str(uuid4()))
    covariates["human_readable_id"] = (covariates.index + 1).astype(str)
    covariates.rename(columns={"chunk_id": "text_unit_id"}, inplace=True)

    return cast(
        pd.DataFrame,
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
