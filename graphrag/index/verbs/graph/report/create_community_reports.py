# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_community_reports and load_strategy methods definition."""

import logging
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

from .strategies.typing import CommunityReportsStrategy

log = logging.getLogger(__name__)


class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


@verb(name="create_community_reports")
async def create_community_reports(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    community_column: str = "community",
    level_column: str = "level",
    input_column: str = "input",
    async_mode: AsyncType = AsyncType.AsyncIO,
    **kwargs,
) -> TableContainer:
    """Generate entities for each row, and optionally a graph of those entities."""
    log.debug("create_community_reports strategy=%s", strategy)
    strategy_type = strategy.get(
        "type", CreateCommunityReportsStrategyType.graph_intelligence
    )
    strategy_exec = load_strategy(strategy_type)
    strategy_args = {**strategy}

    async def run_strategy(row):
        return await strategy_exec(
            row[community_column],
            row[input_column],
            row[level_column],
            callbacks,
            cache,
            strategy_args,
        )

    reports = await derive_from_rows(
        cast(pd.DataFrame, input.get_input()),
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )
    return TableContainer(table=pd.DataFrame(reports))


def load_strategy(
    strategy: CreateCommunityReportsStrategyType,
) -> CommunityReportsStrategy:
    """Load strategy method definition."""
    match strategy:
        case CreateCommunityReportsStrategyType.graph_intelligence:
            from .strategies.graph_intelligence import run

            return run
        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)
