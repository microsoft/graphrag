# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

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
from graphrag.index.verbs.graph.report.strategies.typing import (
    CommunityReport,
    StrategyConfig,
)
from graphrag.llm import CompletionLLM

from .defaults import MOCK_RESPONSES

log = logging.getLogger(__name__)


async def run(
    community: str,
    input: dict,
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
    return await _run_extractor(llm, community, input, args, reporter)


async def _run_extractor(
    llm: CompletionLLM,
    community: str,
    input: dict,
    args: StrategyConfig,
    reporter: VerbCallbacks,
) -> CommunityReport | None:
    extractor = CommunityReportsExtractor(
        llm,
        extraction_prompt=args.get("extraction_prompt", None),
        on_error=lambda e, stack, _data: reporter.error(
            "Community Report Extraction Error", e, stack
        ),
        max_report_length=args.get("max_report_length", None),
    )

    try:
        chain_results = await extractor({
            "input_text": input,
        })

        text_report = chain_results.output
        report = chain_results.structured_output

        if report is not None and len(report.keys()) > 0:
            title = report.get("title", f"Community Report: {community}")
            summary = report.get("summary", "")
            rank = report.get("rating", -1)
            rank_explanation = report.get("rating_explanation")
            findings = report.get("findings", [])

            try:
                rank = float(rank)
            except ValueError:
                log.exception("Error parsing rank: %s defaulting to -1", rank)
                rank = -1

            report_dict = {
                "community": community,
                "title": title,
                "full_content": text_report,
                "summary": summary,
                "rank": rank,
                "rank_explanation": rank_explanation,
                "findings": findings,
                "full_content_json": json.dumps(report, indent=4),
            }
            return CommunityReport(**report_dict)
    except Exception as e:
        log.exception("Error processing community: %s", community)
        reporter.error("Community Report Extraction Error", e, traceback.format_exc())
        return None
