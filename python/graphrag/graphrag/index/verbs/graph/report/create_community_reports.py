#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing create_community_reports and load_strategy methods definition."""
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

from .strategies.typing import CommunityReportsStrategy


class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"


@verb(name="create_community_reports")
async def create_community_reports(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    to: str,
    strategy: dict[str, Any],
    community_column: str = "community",
    level_column: str = "level",
    input_column: str = "input",
    async_mode: AsyncType = AsyncType.AsyncIO,
    **kwargs,
) -> TableContainer:
    """Generate entities for each row, and optionally a graph of those entities."""
    strategy_type = strategy.get(
        "type", CreateCommunityReportsStrategyType.graph_intelligence
    )
    strategy_exec = load_strategy(strategy_type)
    strategy_args = {**strategy}
    levels = input.get_input()[level_column]

    async def run_strategy(row):
        community = await strategy_exec(
            row[community_column], row[input_column], callbacks, cache, strategy_args
        )
        return asdict(cast(Any, community)) if community else None

    reports = await derive_from_rows(
        cast(pd.DataFrame, input.get_input()),
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=kwargs.get("num_threads", 4),
    )
    output = pd.DataFrame({to: reports, level_column: levels})
    return TableContainer(table=output)


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
