# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

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
    base_text_embed = config.get("text_embed", {})
    text_unit_text_embed_config = config.get("text_unit_text_embed", base_text_embed)
    skip_text_unit_embedding = config.get("skip_text_unit_embedding", False)
    covariates_enabled = config.get("covariates_enabled", False)

    others = [
        "workflow:create_final_entities",
        "workflow:create_final_relationships",
    ]
    if covariates_enabled:
        others.append("workflow:create_final_covariates")

    return [
        {
            "verb": "create_final_text_units",
            "args": {
                "skip_embedding": skip_text_unit_embedding,
                "text_embed": text_unit_text_embed_config,
                "covariates_enabled": covariates_enabled,
            },
            "input": {
                "source": "workflow:create_base_text_units",
                "others": others,
            },
        },
    ]
