# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_community_reports and load_strategy methods definition."""

import logging
from collections.abc import Callable

import pandas as pd

import graphrag.data_model.schemas as schemas
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.index.operations.summarize_communities.typing import (
    CommunityReport,
    CommunityReportsStrategy,
    CreateCommunityReportsStrategyType,
)
from graphrag.index.operations.summarize_communities.utils import (
    get_levels,
)
from graphrag.index.utils.derive_from_rows import derive_from_rows
from graphrag.logger.progress import progress_ticker

log = logging.getLogger(__name__)


async def summarize_communities(
    nodes: pd.DataFrame,
    communities: pd.DataFrame,
    local_contexts,
    level_context_builder: Callable,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    strategy: dict,
    max_input_length: int,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
):
    """Generate community summaries."""
    reports: list[CommunityReport | None] = []
    tick = progress_ticker(callbacks.progress, len(local_contexts))
    strategy_exec = load_strategy(strategy["type"])
    strategy_config = {**strategy}

    # if max_retries is not set, inject a dynamically assigned value based on the total number of expected LLM calls to be made
    if strategy_config.get("llm") and strategy_config["llm"]["max_retries"] == -1:
        strategy_config["llm"]["max_retries"] = len(nodes)

    community_hierarchy = (
        communities.explode("children")
        .rename({"children": "sub_community"}, axis=1)
        .loc[:, ["community", "level", "sub_community"]]
    ).dropna()

    levels = get_levels(nodes)

    level_contexts = []
    for level in levels:
        level_context = level_context_builder(
            pd.DataFrame(reports),
            community_hierarchy_df=community_hierarchy,
            local_context_df=local_contexts,
            level=level,
            max_context_tokens=max_input_length,
        )
        level_contexts.append(level_context)

    for level_context in level_contexts:

        async def run_generate(record):
            result = await _generate_report(
                strategy_exec,
                community_id=record[schemas.COMMUNITY_ID],
                community_level=record[schemas.COMMUNITY_LEVEL],
                community_context=record[schemas.CONTEXT_STRING],
                callbacks=callbacks,
                cache=cache,
                strategy=strategy_config,
            )
            tick()
            return result

        local_reports = await derive_from_rows(
            level_context,
            run_generate,
            callbacks=NoopWorkflowCallbacks(),
            num_threads=num_threads,
            async_type=async_mode,
        )
        reports.extend([lr for lr in local_reports if lr is not None])

    return pd.DataFrame(reports)


async def _generate_report(
    runner: CommunityReportsStrategy,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    strategy: dict,
    community_id: int,
    community_level: int,
    community_context: str,
) -> CommunityReport | None:
    """Generate a report for a single community."""
    return await runner(
        community_id,
        community_context,
        community_level,
        callbacks,
        cache,
        strategy,
    )


def load_strategy(
    strategy: CreateCommunityReportsStrategyType,
) -> CommunityReportsStrategy:
    """Load strategy method definition."""
    match strategy:
        case CreateCommunityReportsStrategyType.graph_intelligence:
            from graphrag.index.operations.summarize_communities.strategies import (
                run_graph_intelligence,
            )

            return run_graph_intelligence
        case _:
            msg = f"Unknown strategy: {strategy}"
            raise ValueError(msg)
