# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the extract_covariates verb definition."""

import logging
from dataclasses import asdict
from typing import Any

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
    derive_from_rows,
)

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.operations.extract_covariates.typing import (
    Covariate,
    CovariateExtractStrategy,
    ExtractClaimsStrategyType,
)

log = logging.getLogger(__name__)


DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


async def extract_covariates(
    input: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    column: str,
    covariate_type: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    num_threads: int = 4,
):
    """Extract claims from a piece of text."""
    log.debug("extract_covariates strategy=%s", strategy)
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES

    resolved_entities_map = {}

    strategy = strategy or {}
    strategy_exec = load_strategy(
        strategy.get("type", ExtractClaimsStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    async def run_strategy(row):
        text = row[column]
        result = await strategy_exec(
            text, entity_types, resolved_entities_map, callbacks, cache, strategy_config
        )
        return [
            create_row_from_claim_data(row, item, covariate_type)
            for item in result.covariate_data
        ]

    results = await derive_from_rows(
        input,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=num_threads,
    )
    return pd.DataFrame([item for row in results for item in row or []])


def load_strategy(strategy_type: ExtractClaimsStrategyType) -> CovariateExtractStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case ExtractClaimsStrategyType.graph_intelligence:
            from graphrag.index.operations.extract_covariates.strategies import (
                run_graph_intelligence,
            )

            return run_graph_intelligence
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)


def create_row_from_claim_data(row, covariate_data: Covariate, covariate_type: str):
    """Create a row from the claim data and the input row."""
    return {**row, **asdict(covariate_data), "covariate_type": covariate_type}
