# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_community_reports and load_strategy methods definition."""

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

from .strategies.typing import CommunityReportsStrategy

log = logging.getLogger(__name__)

_NAMED_INPUTS_REQUIRED = "Named inputs are required"
_NODES_INPUT_REQUIRED = "Nodes input is required"
_EDGES_INPUT_REQUIRED = "Edges input is required"
_CLAIMS_INPUT_REQUIRED = "Claims input is required"

class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"


@verb(name="create_community_reports_v2")
async def create_community_reports_v2(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    strategy: dict[str, Any],
    async_mode: AsyncType = AsyncType.AsyncIO,
    **kwargs,
) -> TableContainer:
    """Generate entities for each row, and optionally a graph of those entities."""
    log.debug("create_community_reports strategy=%s", strategy)
    named_inputs = input.named
    if named_inputs is None:
        raise ValueError(_NAMED_INPUTS_REQUIRED)
    
    nodes = named_inputs.get("nodes")
    edges = named_inputs.get("edges")
    claims = named_inputs.get("claims")

    if nodes is None:
        raise ValueError(_NODES_INPUT_REQUIRED)
    if edges is None:
        raise ValueError(_EDGES_INPUT_REQUIRED)
    if claims is None:
        raise ValueError(_CLAIMS_INPUT_REQUIRED)
    

    print("nodes", nodes)
    # strategy_type = strategy.get(
    #     "type", CreateCommunityReportsStrategyType.graph_intelligence
    # )
    # strategy_exec = load_strategy(strategy_type)
    # strategy_args = {**strategy}
    # levels = input.get_input()[level_column]

    # async def run_strategy(row):
    #     community = await strategy_exec(
    #         row[community_column], row[input_column], callbacks, cache, strategy_args
    #     )
    #     return asdict(cast(Any, community)) if community else None

    # reports = await derive_from_rows(
    #     cast(pd.DataFrame, input.get_input()),
    #     run_strategy,
    #     callbacks,
    #     scheduling_type=async_mode,
    #     num_threads=kwargs.get("num_threads", 4),
    # )
    # output = pd.DataFrame({to: reports, level_column: levels})
    return TableContainer(table=pd.DataFrame())

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
