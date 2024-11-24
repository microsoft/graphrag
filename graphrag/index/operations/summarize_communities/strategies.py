# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run, _run_extractor and _load_nodes_edges_for_claim_chain methods definition."""

import json
import logging
import traceback

from datashaper import VerbCallbacks

from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.graph.extractors.community_reports import (
    CommunityReportsExtractor,
)
from graphrag.index.llm.load_llm import load_llm
from graphrag.index.operations.summarize_communities.typing import (
    CommunityReport,
    StrategyConfig,
)
from graphrag.index.utils.rate_limiter import RateLimiter
from graphrag.llm import CompletionLLM

DEFAULT_CHUNK_SIZE = 3000

log = logging.getLogger(__name__)


async def run_graph_intelligence(
    community: str | int,
    input: str,
    level: int,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    args: StrategyConfig,
) -> CommunityReport | None:
    """Run the graph intelligence entity extraction strategy."""
    llm_config = args.get("llm", {})
    llm_type = llm_config.get("type")
    llm = load_llm("community_reporting", llm_type, callbacks, cache, llm_config)
    return await _run_extractor(llm, community, input, level, args, callbacks)


async def _run_extractor(
    llm: CompletionLLM,
    community: str | int,
    input: str,
    level: int,
    args: StrategyConfig,
    callbacks: VerbCallbacks,
) -> CommunityReport | None:
    # RateLimiter
    rate_limiter = RateLimiter(rate=1, per=60)
    extractor = CommunityReportsExtractor(
        llm,
        extraction_prompt=args.get("extraction_prompt", None),
        max_report_length=args.get("max_report_length", None),
        on_error=lambda e, stack, _data: callbacks.error(
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
            full_content_json=json.dumps(report, indent=4, ensure_ascii=False),
        )
    except Exception as e:
        log.exception("Error processing community: %s", community)
        callbacks.error("Community Report Extraction Error", e, traceback.format_exc())
        return None


def _parse_rank(report: dict) -> float:
    rank = report.get("rating", -1)
    try:
        return float(rank)
    except ValueError:
        log.exception("Error parsing rank: %s defaulting to -1", rank)
        return -1
