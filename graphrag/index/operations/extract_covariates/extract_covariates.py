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
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.index.operations.extract_covariates.claim_extractor import ClaimExtractor
from graphrag.index.operations.extract_covariates.typing import (
    Covariate,
    CovariateExtractionResult,
)
from graphrag.index.utils.derive_from_rows import derive_from_rows
from graphrag.language_model.manager import ModelManager

logger = logging.getLogger(__name__)


DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


async def extract_covariates(
    input: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    model_config: LanguageModelConfig,
    column: str,
    covariate_type: str,
    max_gleanings: int,
    claim_description: str,
    prompt: str,
    entity_types: list[str] | None = None,
):
    """Extract claims from a piece of text."""
    if entity_types is None:
        entity_types = DEFAULT_ENTITY_TYPES

    resolved_entities_map = {}

    async def run_strategy(row):
        text = row[column]
        result = await run_extract_claims(
            input=text,
            entity_types=entity_types,
            resolved_entities_map=resolved_entities_map,
            callbacks=callbacks,
            cache=cache,
            model_config=model_config,
            max_gleanings=max_gleanings,
            claim_description=claim_description,
            prompt=prompt,
        )
        return [
            create_row_from_claim_data(row, item, covariate_type)
            for item in result.covariate_data
        ]

    results = await derive_from_rows(
        input,
        run_strategy,
        callbacks,
        async_type=model_config.async_mode,
        num_threads=model_config.concurrent_requests,
        progress_msg="extract covariates progress: ",
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
    model_config: LanguageModelConfig,
    max_gleanings: int,
    claim_description: str,
    prompt: str,
) -> CovariateExtractionResult:
    """Run the Claim extraction chain."""
    model = ModelManager().get_or_create_chat_model(
        name="extract_claims",
        model_type=model_config.type,
        config=model_config,
        callbacks=callbacks,
        cache=cache,
    )

    extractor = ClaimExtractor(
        model=model,
        extraction_prompt=prompt,
        max_gleanings=max_gleanings,
        on_error=lambda e, s, d: logger.error(
            "Claim Extraction Error", exc_info=e, extra={"stack": s, "details": d}
        ),
    )

    input = [input] if isinstance(input, str) else input

    results = await extractor(
        texts=input,
        entity_spec=entity_types,
        resolved_entities=resolved_entities_map,
        claim_description=claim_description,
    )

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
