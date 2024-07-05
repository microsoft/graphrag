# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run, _run_extractor and _load_nodes_edges_for_claim_chain methods definition."""

import json
import logging
import traceback

from datashaper import VerbCallbacks

from graphrag.config.enums import LLMType
from graphrag.index.cache import PipelineCache
from graphrag.index.graph.extractors.community_reports import (
    CommunityReportsExtractor,
)
from graphrag.index.llm import load_llm
from graphrag.index.utils.rate_limiter import RateLimiter
from graphrag.index.verbs.graph.report.strategies.typing import (
    CommunityReport,
    StrategyConfig,
)
from graphrag.llm import CompletionLLM

from .defaults import MOCK_RESPONSES

log = logging.getLogger(__name__)


async def run(
    community: str | int,
    input: str,
    level: int,
    reporter: VerbCallbacks,
    pipeline_cache: PipelineCache,
    args: StrategyConfig,
) -> CommunityReport | None:
    """Run the graph intelligence entity extraction strategy."""
    llm_config = args.get(
        "llm", {"type": LLMType.StaticResponse, "responses": MOCK_RESPONSES}
    )
    llm_type = llm_config.get("type", LLMType.StaticResponse)
    llm = load_llm(
        "community_reporting", llm_type, reporter, pipeline_cache, llm_config
    )
    return await _run_extractor(llm, community, input, level, args, reporter)


async def _run_extractor(
    llm: CompletionLLM,
    community: str | int,
    input: str,
    level: int,
    args: StrategyConfig,
    reporter: VerbCallbacks,
) -> CommunityReport | None:
    # RateLimiter
    rate_limiter = RateLimiter(rate=1, per=60)
    extractor = CommunityReportsExtractor(
        llm,
        extraction_prompt=args.get("extraction_prompt", None),
        max_report_length=args.get("max_report_length", None),
        on_error=lambda e, stack, _data: reporter.error(
            "Community Report Extraction Error", e, stack
        ),
    )

    try:
        await rate_limiter.acquire()
        results = await extractor({"input_text": input})
        report = results.structured_output
        if report is None or len(report.keys()) == 0:
            log.warning("No report found for community: %s", community)
            return None

        return CommunityReport(
            community=community,
            full_content=results.output,
            level=level,
            rank=_parse_rank(report),
            title=report.get("title", f"Community Report: {community}"),
            rank_explanation=report.get("rating_explanation", ""),
            summary=report.get("summary", ""),
            findings=report.get("findings", []),
            full_content_json=json.dumps(report, indent=4),
        )
    except Exception as e:
        log.exception("Error processing community: %s", community)
        reporter.error("Community Report Extraction Error", e, traceback.format_exc())
        return None


def _parse_rank(report: dict) -> float:
    rank = report.get("rating", -1)
    try:
        return float(rank)
    except ValueError:
        log.exception("Error parsing rank: %s defaulting to -1", rank)
        return -1
