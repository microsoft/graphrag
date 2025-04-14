# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the extract_covariates verb definition."""

import logging
from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import AsyncType
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.index.operations.extract_covariates.claim_extractor import ClaimExtractor
from graphrag.index.operations.extract_covariates.typing import (
    Covariate,
    CovariateExtractionResult,
)
from graphrag.index.utils.derive_from_rows import derive_from_rows
from graphrag.language_model.manager import ModelManager

log = logging.getLogger(__name__)


DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


async def extract_covariates(
    input: pd.DataFrame,
    callbacks: WorkflowCallbacks,
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

    # if max_retries is not set, inject a dynamically assigned value based on the total number of expected LLM calls to be made
    if strategy_config.get("llm") and strategy_config["llm"]["max_retries"] == -1:
        strategy_config["llm"]["max_retries"] = len(input)

    async def run_strategy(row):
        text = row[column]
        result = await run_extract_claims(
            input=text,
            entity_types=entity_types,
            resolved_entities_map=resolved_entities_map,
            callbacks=callbacks,
            cache=cache,
            strategy_config=strategy_config,
        )
        return [
            create_row_from_claim_data(row, item, covariate_type)
            for item in result.covariate_data
        ]

    results = await derive_from_rows(
        input,
        run_strategy,
        callbacks,
        async_type=async_mode,
        num_threads=num_threads,
    )
    return pd.DataFrame([item for row in results for item in row or []])


def create_row_from_claim_data(row, covariate_data: Covariate, covariate_type: str):
    """Create a row from the claim data and the input row."""
    return {**row, **asdict(covariate_data), "covariate_type": covariate_type}


async def run_extract_claims(
    input: str | Iterable[str],
    entity_types: list[str],
    resolved_entities_map: dict[str, str],
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    strategy_config: dict[str, Any],
) -> CovariateExtractionResult:
    """Run the Claim extraction chain."""
    llm_config = LanguageModelConfig(**strategy_config["llm"])
    llm = ModelManager().get_or_create_chat_model(
        name="extract_claims",
        model_type=llm_config.type,
        config=llm_config,
        callbacks=callbacks,
        cache=cache,
    )

    extraction_prompt = strategy_config.get("extraction_prompt")
    max_gleanings = strategy_config.get(
        "max_gleanings", graphrag_config_defaults.extract_claims.max_gleanings
    )
    tuple_delimiter = strategy_config.get("tuple_delimiter")
    record_delimiter = strategy_config.get("record_delimiter")
    completion_delimiter = strategy_config.get("completion_delimiter")

    extractor = ClaimExtractor(
        model_invoker=llm,
        extraction_prompt=extraction_prompt,
        max_gleanings=max_gleanings,
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
