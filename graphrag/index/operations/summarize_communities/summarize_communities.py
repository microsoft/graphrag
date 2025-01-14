# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing create_community_reports and load_strategy methods definition."""

import logging

import pandas as pd

import graphrag.config.defaults as defaults
import graphrag.index.operations.summarize_communities.community_reports_extractor.schemas as schemas
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.index.operations.summarize_communities.community_reports_extractor import (
    prep_community_report_context,
)
from graphrag.index.operations.summarize_communities.community_reports_extractor.utils import (
    get_levels,
)
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
    nodes,
    community_hierarchy,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
):
    """Generate community summaries."""
    levels = get_levels(nodes)
    reports: list[CommunityReport | None] = []
    tick = progress_ticker(callbacks.progress, len(local_contexts))
    runner = load_strategy(strategy["type"])

    for level in levels:
        level_contexts = prep_community_report_context(
            pd.DataFrame(reports),
            local_context_df=local_contexts,
            community_hierarchy_df=community_hierarchy,
            level=level,
            max_tokens=strategy.get(
                "max_input_tokens", defaults.COMMUNITY_REPORT_MAX_INPUT_LENGTH
            ),
        )

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
            level_contexts,
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
