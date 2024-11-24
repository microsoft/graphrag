# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import (
    AsyncType,
)

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_covariates"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final covariates table.

    ## Dependencies
    * `workflow:create_base_text_units`
    """
    claim_extract_config = config.get("claim_extract", {})
    extraction_strategy = claim_extract_config.get("strategy")
    async_mode = claim_extract_config.get("async_mode", AsyncType.AsyncIO)
    num_threads = claim_extract_config.get("num_threads")

    return [
        {
            "verb": "create_final_covariates",
            "args": {
                "covariate_type": "claim",
                "extraction_strategy": extraction_strategy,
                "async_mode": async_mode,
                "num_threads": num_threads,
            },
            "input": {"source": "workflow:create_base_text_units"},
        },
    ]
