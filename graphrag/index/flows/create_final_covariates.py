# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any
from uuid import uuid4

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
)

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.extract_covariates import (
    extract_covariates,
)


async def create_final_covariates(
    text_units: pd.DataFrame,
    callbacks: VerbCallbacks,
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
    covariates = await extract_covariates(
        text_units,
        callbacks,
        cache,
        "text",
        covariate_type,
        extraction_strategy,
        async_mode,
        entity_types,
        num_threads,
    )
    text_units.drop(columns=["text_unit_id"], inplace=True)  # don't pollute the global
    covariates["id"] = covariates["covariate_type"].apply(lambda _x: str(uuid4()))
    covariates["human_readable_id"] = covariates.index + 1

    return covariates.loc[
        :,
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
        ],
    ]
