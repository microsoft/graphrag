# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _run_chain methods definitions."""

from collections.abc import Iterable
from typing import Any

from datashaper import VerbCallbacks

from graphrag.config.enums import LLMType
from graphrag.index.cache import PipelineCache
from graphrag.index.graph.extractors.claims import ClaimExtractor
from graphrag.index.llm import load_llm
from graphrag.index.verbs.covariates.typing import (
    Covariate,
    CovariateExtractionResult,
)
from graphrag.llm import CompletionLLM

from .defaults import MOCK_LLM_RESPONSES


async def run(
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
    max_gleanings = strategy_config.get("max_gleanings", 0)
    tuple_delimiter = strategy_config.get("tuple_delimiter")
    record_delimiter = strategy_config.get("record_delimiter")
    completion_delimiter = strategy_config.get("completion_delimiter")
    encoding_model = strategy_config.get("encoding_name")

    extractor = ClaimExtractor(
        llm_invoker=llm,
        extraction_prompt=extraction_prompt,
        max_gleanings=max_gleanings,
        encoding_model=encoding_model,
        on_error=lambda e, s, d: reporter.error("Claim Extraction Error", e, s, d)
        if reporter
        else None,
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
        subject_type=item.get("subject_type"),
        object_id=item.get("object_id"),
        object_type=item.get("object_type"),
        type=item.get("type"),
        status=item.get("status"),
        start_date=item.get("start_date"),
        end_date=item.get("end_date"),
        description=item.get("description"),
        source_text=item.get("source_text"),
        doc_id=item.get("doc_id"),
        record_id=item.get("record_id"),
        id=item.get("id"),
    )
