# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_community_reports and load_strategy methods definition."""

import logging

import pandas as pd

import graphrag.index.operations.summarize_communities.community_reports_extractor.schemas as schemas
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.index.operations.summarize_communities.typing import (
    CommunityReport,
    CommunityReportsStrategy,
    CreateCommunityReportsStrategyType,
)
from graphrag.index.run.derive_from_rows import derive_from_rows
from graphrag.logger.progress import progress_ticker

log = logging.getLogger(__name__)


async def summarize_communities(
    local_contexts,
    level_contexts,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
):
    """Generate community summaries."""
    reports: list[CommunityReport | None] = []
    tick = progress_ticker(callbacks.progress, len(local_contexts))
    runner = load_strategy(strategy["type"])

    for level_context in level_contexts:

        async def run_generate(record):
            result = await _generate_report(
                runner,
                community_id=record[schemas.NODE_COMMUNITY],
                community_level=record[schemas.COMMUNITY_LEVEL],
                community_context=record[schemas.CONTEXT_STRING],
                callbacks=callbacks,
                cache=cache,
                strategy=strategy,
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
