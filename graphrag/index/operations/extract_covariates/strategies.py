# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run and _run_chain methods definitions."""

from collections.abc import Iterable
from typing import Any

from datashaper import VerbCallbacks

import graphrag.config.defaults as defs
from graphrag.index.cache.pipeline_cache import PipelineCache
from graphrag.index.graph.extractors.claims import ClaimExtractor
from graphrag.index.llm.load_llm import load_llm
from graphrag.index.operations.extract_covariates.typing import (
    Covariate,
    CovariateExtractionResult,
)
from graphrag.llm import CompletionLLM


async def run_graph_intelligence(
    input: str | Iterable[str],
    entity_types: list[str],
    resolved_entities_map: dict[str, str],
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy_config: dict[str, Any],
) -> CovariateExtractionResult:
    """Run the Claim extraction chain."""
    llm_config = strategy_config.get("llm", {})
    llm_type = llm_config.get("type")
    llm = load_llm("claim_extraction", llm_type, callbacks, cache, llm_config)
    return await _execute(
        llm, input, entity_types, resolved_entities_map, callbacks, strategy_config
    )


async def _execute(
    llm: CompletionLLM,
    texts: Iterable[str],
    entity_types: list[str],
    resolved_entities_map: dict[str, str],
    callbacks: VerbCallbacks,
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
            callbacks.error("Claim Extraction Error", e, s, d) if callbacks else None
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
