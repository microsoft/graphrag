# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the extract_covariates verb definition."""

import logging
from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

import pandas as pd
from datashaper import (
    AsyncType,
    VerbCallbacks,
    derive_from_rows,
)

import graphrag.config.defaults as defs
from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.llm.load_llm import load_llm, read_llm_params
from graphrag.index.operations.extract_covariates.claim_extractor import ClaimExtractor
from graphrag.index.operations.extract_covariates.typing import (
    Covariate,
    CovariateExtractionResult,
)

log = logging.getLogger(__name__)


DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


async def extract_covariates(
    input: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    column: str,
    covariate_type: str,
    strategy: dict[str, Any] | None,
    async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    num_threads: int = 4,
):
    """Extract claims from a piece of text."""
    log.debug("extract_covariates strategy=%s", strategy)
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES

    resolved_entities_map = {}

    strategy = strategy or {}
    strategy_config = {**strategy}

    async def run_strategy(row):
        text = row[column]
        result = await run_claim_extraction(
            text, entity_types, resolved_entities_map, callbacks, cache, strategy_config
        )
        return [
            create_row_from_claim_data(row, item, covariate_type)
            for item in result.covariate_data
        ]

    results = await derive_from_rows(
        input,
        run_strategy,
        callbacks,
        scheduling_type=async_mode,
        num_threads=num_threads,
    )
    return pd.DataFrame([item for row in results for item in row or []])


def create_row_from_claim_data(row, covariate_data: Covariate, covariate_type: str):
    """Create a row from the claim data and the input row."""
    return {**row, **asdict(covariate_data), "covariate_type": covariate_type}


async def run_claim_extraction(
    input: str | Iterable[str],
    entity_types: list[str],
    resolved_entities_map: dict[str, str],
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    strategy_config: dict[str, Any],
) -> CovariateExtractionResult:
    """Run the Claim extraction chain."""
    llm_config = read_llm_params(strategy_config.get("llm", {}))
    llm = load_llm("claim_extraction", llm_config, callbacks=callbacks, cache=cache)
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

    input = [input] if isinstance(input, str) else input

    results = await extractor({
        "input_text": input,
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
