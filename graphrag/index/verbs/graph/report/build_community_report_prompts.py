# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing create_community_reports and load_strategy methods definition."""

import logging
from enum import Enum
from typing import cast

import pandas as pd
from datashaper import (
    AsyncType,
    NoopVerbCallbacks,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    derive_from_rows,
    progress_ticker,
    verb,
)

import graphrag.index.verbs.graph.report.schemas as schemas
from graphrag.config.enums import LLMType
from graphrag.index.cache import PipelineCache
from graphrag.index.llm import load_llm
from graphrag.llm import CompletionLLM

from .prep_community_report_context import prep_community_report_context
from .prompts import COMMUNITY_REPORT_PROMPT as extraction_prompt

log = logging.getLogger(__name__)

_NAMED_INPUTS_REQUIRED = "Named inputs are required"


class CreateCommunityReportsStrategyType(str, Enum):
    """CreateCommunityReportsStrategyType class definition."""

    graph_intelligence = "graph_intelligence"


@verb(name="build_community_report_prompts")
async def build_community_report_prompts(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    max_tokens: int = 16_000,
    num_threads: int = 4,
    **_kwargs,
) -> TableContainer:
    """Generate entities for each row, and optionally a graph of those entities."""
    log.debug("create_community_reports strategy=%s", strategy)
    named_inputs = input.named
    if named_inputs is None:
        raise ValueError(_NAMED_INPUTS_REQUIRED)

    def get_table(name: str) -> pd.DataFrame:
        container = named_inputs.get(name)
        if container is None:
            msg = f"Missing input: {name}"
            raise ValueError(msg)
        return cast(pd.DataFrame, container.table)

    nodes = get_table("nodes")
    community_hierarchy = get_table("community_hierarchy")
    local_contexts = cast(pd.DataFrame, input.get_input())
    levels = sorted(nodes[schemas.NODE_LEVEL].unique(), reverse=True)

    reports: list[dict | None] = []
    tick = progress_ticker(callbacks.progress, len(local_contexts))

    llm = get_llm(callbacks, cache, strategy.get("llm") or {})

    for level in levels:
        level_contexts = prep_community_report_context(
            local_context_df=local_contexts,
            community_hierarchy_df=community_hierarchy,
            level=level,
            max_tokens=max_tokens,
        )

        async def run_generate(record):
            result = await _generate_report(
                llm=llm,
                community_id=record[schemas.NODE_COMMUNITY],
                community_level=record[schemas.COMMUNITY_LEVEL],
                community_context=record[schemas.CONTEXT_STRING],
            )
            tick()
            return result

        local_reports = await derive_from_rows(
            level_contexts,
            run_generate,
            callbacks=NoopVerbCallbacks(),
            num_threads=num_threads,
            scheduling_type=async_mode,
        )
        reports.extend(local_reports)

    return TableContainer(table=pd.DataFrame(reports))


def get_llm(
    reporter: VerbCallbacks,
    pipeline_cache: PipelineCache,
    llm_config: dict,
) -> CompletionLLM:
    """Get the LLM instance."""
    llm_type = llm_config.get("type", LLMType.OpenAIChat)
    return load_llm("community_reports", llm_type, reporter, pipeline_cache, llm_config)


async def _generate_report(
    llm: CompletionLLM,
    community_id: int | str,
    community_level: int | str,
    community_context: str,
) -> dict:
    """Generate a report for a single community."""

    def finding_summary(finding: dict):
        if isinstance(finding, str):
            return finding
        return finding.get("summary")

    def finding_explanation(finding: dict):
        if isinstance(finding, str):
            return ""
        return finding.get("explanation")

    response = await llm(
        extraction_prompt, variables={"input_text": community_context}, json=True
    )
    response = response.json or {}

    title = response.get("title", "Report")
    summary = response.get("summary", "")
    findings = response.get("findings", [])
    rating = response.get("rating", 0.0)
    rating_explanation = response.get("rating_explanation", "")
    report_sections = "\n\n".join(
        f"## {finding_summary(f)}\n\n{finding_explanation(f)}" for f in findings
    )
    full_content = f"# {title}\n\n{summary}\n\n{report_sections}"
    return {
        schemas.REPORT_ID: str(community_id),
        schemas.COMMUNITY_ID: community_id,
        schemas.COMMUNITY_LEVEL: community_level,
        schemas.TITLE: title,
        schemas.SUMMARY: summary,
        schemas.FINDINGS: findings,
        schemas.RATING: rating,
        schemas.EXPLANATION: rating_explanation,
        schemas.FULL_CONTENT: full_content,
        schemas.FULL_CONTENT_JSON: response,
        schemas.CONTEXT_STRING: community_context,
    }
