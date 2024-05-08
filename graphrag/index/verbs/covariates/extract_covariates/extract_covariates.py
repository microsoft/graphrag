# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the extract_covariates verb definition."""

import logging
from dataclasses import asdict
from enum import Enum
from typing import Any, cast

import pandas as pd
from datashaper import (
    AsyncType,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    derive_from_rows,
    verb,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.verbs.covariates.typing import Covariate, CovariateExtractStrategy

log = logging.getLogger(__name__)


class ExtractClaimsStrategyType(str, Enum):
    """ExtractClaimsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


@verb(name="extract_covariates")
async def extract_covariates(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    column: str,
    covariate_type: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    **kwargs,
) -> TableContainer:
    """
    Extract claims from a piece of text.

    ## Usage
    TODO
    """
    log.debug("extract_covariates strategy=%s", strategy)
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES
    output = cast(pd.DataFrame, input.get_input())

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
        output,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )
    output = pd.DataFrame([item for row in results for item in row or []])
    return TableContainer(table=output)


def load_strategy(strategy_type: ExtractClaimsStrategyType) -> CovariateExtractStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case ExtractClaimsStrategyType.graph_intelligence:
            from .strategies.graph_intelligence import run as run_gi

            return run_gi
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)


def create_row_from_claim_data(row, covariate_data: Covariate, covariate_type: str):
    """Create a row from the claim data and the input row."""
    item = {**row, **asdict(covariate_data), "covariate_type": covariate_type}
    # TODO: doc_id from extraction isn't necessary
    # since chunking happens before this
    del item["doc_id"]
    return item
