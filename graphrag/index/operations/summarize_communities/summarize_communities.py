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
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.index.operations.summarize_communities.community_reports_extractor import (
    CommunityReportsExtractor,
)
from graphrag.index.operations.summarize_communities.typing import (
    CommunityReport,
    CommunityReportsStrategy,
    Finding,
)
from graphrag.index.operations.summarize_communities.utils import (
    get_levels,
)
from graphrag.index.utils.derive_from_rows import derive_from_rows
from graphrag.language_model.manager import ModelManager
from graphrag.logger.progress import progress_ticker
from graphrag.tokenizer.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


async def summarize_communities(
    nodes: pd.DataFrame,
    communities: pd.DataFrame,
    local_contexts,
    level_context_builder: Callable,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    prompt: str,
    tokenizer: Tokenizer,
    max_input_length: int,
    max_report_length: int,
):
    """Generate community summaries."""
    reports: list[CommunityReport | None] = []
    tick = progress_ticker(callbacks.progress, len(local_contexts))
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
            tokenizer=tokenizer,
            max_context_tokens=max_input_length,
        )
        level_contexts.append(level_context)

    for i, level_context in enumerate(level_contexts):

        async def run_generate(record):
            result = await _generate_report(
                run_extractor,
                community_id=record[schemas.COMMUNITY_ID],
                community_level=record[schemas.COMMUNITY_LEVEL],
                community_context=record[schemas.CONTEXT_STRING],
                callbacks=callbacks,
                cache=cache,
                model_config=model_config,
                extraction_prompt=prompt,
                max_report_length=max_report_length,
            )
            tick()
            return result

        local_reports = await derive_from_rows(
            level_context,
            run_generate,
            callbacks=NoopWorkflowCallbacks(),
            num_threads=model_config.concurrent_requests,
            async_type=model_config.async_mode,
            progress_msg=f"level {levels[i]} summarize communities progress: ",
        )
        reports.extend([lr for lr in local_reports if lr is not None])

    return pd.DataFrame(reports)


async def _generate_report(
    runner: CommunityReportsStrategy,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    extraction_prompt: str,
    community_id: int,
    community_level: int,
    community_context: str,
    max_report_length: int,
) -> CommunityReport | None:
    """Generate a report for a single community."""
    return await runner(
        community_id,
        community_context,
        community_level,
        callbacks,
        cache,
        model_config,
        extraction_prompt,
        max_report_length,
    )


async def run_extractor(
    community: str | int,
    input: str,
    level: int,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    extraction_prompt: str,
    max_report_length: int,
) -> CommunityReport | None:
    """Run the graph intelligence entity extraction strategy."""
    model = ModelManager().get_or_create_chat_model(
        name="community_reporting",
        model_type=model_config.type,
        config=model_config,
        callbacks=callbacks,
        cache=cache,
    )

    extractor = CommunityReportsExtractor(
        model,
        extraction_prompt=extraction_prompt,
        max_report_length=max_report_length,
        on_error=lambda e, stack, _data: logger.error(
            "Community Report Extraction Error", exc_info=e, extra={"stack": stack}
        ),
    )

    try:
        results = await extractor(input)
        report = results.structured_output
        if report is None:
            logger.warning("No report found for community: %s", community)
            return None

        return CommunityReport(
            community=community,
            full_content=results.output,
            level=level,
            rank=report.rating,
            title=report.title,
            rating_explanation=report.rating_explanation,
            summary=report.summary,
            findings=[
                Finding(explanation=f.explanation, summary=f.summary)
                for f in report.findings
            ],
            full_content_json=report.model_dump_json(indent=4),
        )
    except Exception:
        logger.exception("Error processing community: %s", community)
        return None
