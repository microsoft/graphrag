# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _run_chain methods definitions."""

from collections.abc import Iterable
from typing import Any

from datashaper import VerbCallbacks

import graphrag.config.defaults as defs
from graphrag.config.enums import LLMType
from graphrag.index.cache import PipelineCache
from graphrag.index.graph.extractors.claims import ClaimExtractor
from graphrag.index.llm import load_llm
from graphrag.llm import CompletionLLM

from .typing import (
    Covariate,
    CovariateExtractionResult,
)

MOCK_LLM_RESPONSES = [
    """
(COMPANY A<|>GOVERNMENT AGENCY B<|>ANTI-COMPETITIVE PRACTICES<|>TRUE<|>2022-01-10T00:00:00<|>2022-01-10T00:00:00<|>Company A was found to engage in anti-competitive practices because it was fined for bid rigging in multiple public tenders published by Government Agency B according to an article published on 2022/01/10<|>According to an article published on 2022/01/10, Company A was fined for bid rigging while participating in multiple public tenders published by Government Agency B.)
    """.strip()
]


async def run_graph_intelligence(
    input: str | Iterable[str],
    entity_types: list[str],
    resolved_entities_map: dict[str, str],
    reporter: VerbCallbacks,
    pipeline_cache: PipelineCache,
    strategy_config: dict[str, Any],
) -> CovariateExtractionResult:
    """Run the Claim extraction chain."""
    llm_config = strategy_config.get(
        "llm", {"type": LLMType.StaticResponse, "responses": MOCK_LLM_RESPONSES}
    )
    llm_type = llm_config.get("type", LLMType.StaticResponse)
    llm = load_llm("claim_extraction", llm_type, reporter, pipeline_cache, llm_config)
    return await _execute(
        llm, input, entity_types, resolved_entities_map, reporter, strategy_config
    )


async def _execute(
    llm: CompletionLLM,
    texts: Iterable[str],
    entity_types: list[str],
    resolved_entities_map: dict[str, str],
    reporter: VerbCallbacks,
    strategy_config: dict[str, Any],
) -> CovariateExtractionResult:
    extraction_prompt = strategy_config.get("extraction_prompt")
    max_gleanings = strategy_config.get("max_gleanings", defs.CLAIM_MAX_GLEANINGS)
    tuple_delimiter = strategy_config.get("tuple_delimiter")
    record_delimiter = strategy_config.get("record_delimiter")
    completion_delimiter = strategy_config.get("completion_delimiter")
    encoding_model = strategy_config.get("encoding_name")

    extractor = ClaimExtractor(
        llm_invoker=llm,
        extraction_prompt=extraction_prompt,
        max_gleanings=max_gleanings,
        encoding_model=encoding_model,
        on_error=lambda e, s, d: (
            reporter.error("Claim Extraction Error", e, s, d) if reporter else None
        ),
    )

    claim_description = strategy_config.get("claim_description")
    if claim_description is None:
        msg = "claim_description is required for claim extraction"
        raise ValueError(msg)

    texts = [texts] if isinstance(texts, str) else texts

    results = await extractor({
        "input_text": texts,
        "entity_specs": entity_types,
        "resolved_entities": resolved_entities_map,
        "claim_description": claim_description,
        "tuple_delimiter": tuple_delimiter,
        "record_delimiter": record_delimiter,
        "completion_delimiter": completion_delimiter,
    })

    claim_data = results.output
    return CovariateExtractionResult([create_covariate(item) for item in claim_data])


def create_covariate(item: dict[str, Any]) -> Covariate:
    """Create a covariate from the item."""
    return Covariate(
        subject_id=item.get("subject_id"),
        object_id=item.get("object_id"),
        type=item.get("type"),
        status=item.get("status"),
        start_date=item.get("start_date"),
        end_date=item.get("end_date"),
        description=item.get("description"),
        source_text=item.get("source_text"),
        record_id=item.get("record_id"),
        id=item.get("id"),
    )
