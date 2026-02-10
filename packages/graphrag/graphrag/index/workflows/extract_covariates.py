# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from typing import TYPE_CHECKING
from uuid import uuid4

import pandas as pd
from graphrag_llm.completion import create_completion

from graphrag.cache.cache_key_creator import cache_key_creator
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.defaults import DEFAULT_ENTITY_TYPES
from graphrag.config.enums import AsyncType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
from graphrag.data_model.schemas import COVARIATES_FINAL_COLUMNS
from graphrag.index.operations.extract_covariates.extract_covariates import (
    extract_covariates as extractor,
)
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to extract and format covariates."""
    logger.info("Workflow started: extract_covariates")
    output = None
    if config.extract_claims.enabled:
        reader = DataReader(context.output_table_provider)
        text_units = await reader.text_units()

        model_config = config.get_completion_model_config(
            config.extract_claims.completion_model_id
        )

        model = create_completion(
            model_config,
            cache=context.cache.child(config.extract_claims.model_instance_name),
            cache_key_creator=cache_key_creator,
        )

        prompts = config.extract_claims.resolved_prompts()

        output = await extract_covariates(
            text_units=text_units,
            callbacks=context.callbacks,
            model=model,
            covariate_type="claim",
            max_gleanings=config.extract_claims.max_gleanings,
            claim_description=config.extract_claims.description,
            prompt=prompts.extraction_prompt,
            entity_types=DEFAULT_ENTITY_TYPES,
            num_threads=config.concurrent_requests,
            async_type=config.async_mode,
        )

        await context.output_table_provider.write_dataframe("covariates", output)

    logger.info("Workflow completed: extract_covariates")
    return WorkflowFunctionOutput(result=output)


async def extract_covariates(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    model: "LLMCompletion",
    covariate_type: str,
    max_gleanings: int,
    claim_description: str,
    prompt: str,
    entity_types: list[str],
    num_threads: int,
    async_type: AsyncType,
) -> pd.DataFrame:
    """All the steps to extract and format covariates."""
    # reassign the id because it will be overwritten in the output by a covariate one
    # this also results in text_unit_id being copied to the output covariate table
    text_units["text_unit_id"] = text_units["id"]

    covariates = await extractor(
        input=text_units,
        callbacks=callbacks,
        model=model,
        column="text",
        covariate_type=covariate_type,
        max_gleanings=max_gleanings,
        claim_description=claim_description,
        prompt=prompt,
        entity_types=entity_types,
        num_threads=num_threads,
        async_type=async_type,
    )
    text_units.drop(columns=["text_unit_id"], inplace=True)  # don't pollute the global
    covariates["id"] = covariates["covariate_type"].apply(lambda _x: str(uuid4()))
    covariates["human_readable_id"] = covariates.index

    return covariates.loc[:, COVARIATES_FINAL_COLUMNS]
