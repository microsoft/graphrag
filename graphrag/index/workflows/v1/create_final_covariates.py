# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import AsyncType

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_covariates"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final covariates table.

    ## Dependencies
    * `workflow:create_base_text_units`
    * `workflow:create_base_extracted_entities`
    """
    claim_extract_config = config.get("claim_extract", {})
    chunk_column = config.get("chunk_column", "chunk")
    chunk_id_column = config.get("chunk_id_column", "chunk_id")
    async_mode = config.get("async_mode", AsyncType.AsyncIO)
    return [
        {
            "verb": "create_final_covariates",
            "args": {
                "column": chunk_column,
                "id_column": chunk_id_column,
                "covariate_type": "claim",
                "async_mode": async_mode,
                **claim_extract_config,
            },
            "input": {"source": "workflow:create_base_text_units"},
        },
    ]
