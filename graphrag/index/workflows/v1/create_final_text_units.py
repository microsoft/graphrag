# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final text-units table.

    ## Dependencies
    * `workflow:create_base_text_units`
    * `workflow:create_final_entities`
    * `workflow:create_final_communities`
    """
    covariates_enabled = config.get("covariates_enabled", False)

    input = {
        "source": "workflow:create_base_text_units",
        "entities": "workflow:create_final_entities",
        "relationships": "workflow:create_final_relationships",
    }

    if covariates_enabled:
        input["covariates"] = "workflow:create_final_covariates"

    return [
        {
            "verb": "create_final_text_units",
            "args": {},
            "input": input,
        },
    ]
